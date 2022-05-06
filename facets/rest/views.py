import hashlib
import urllib
import json, os

from rest_framework import viewsets

from django.utils.dateformat import DateFormat

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.decorators import api_view, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import *

from rest_framework import renderers
from rest_framework.schemas import AutoSchema, ManualSchema

from django.conf.global_settings import LOGGING
import logging

from rest.models import *

from lib.process import ScoreProcessing

from lib.search.IndexWrapper import IndexWrapper

from lib.search.SearchContext import *

# Get an instance of a logger
logger = logging.getLogger(__name__)


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs["content_type"] = "application/json"
        super(JSONResponse, self).__init__(content, **kwargs)


@csrf_exempt
@api_view(["GET"])
def welcome(request):
    """
    Welcome message to the services area
    """
    return JSONResponse({"Message": "Welcome to Facets web services root URL"})

@csrf_exempt
@api_view(["GET", "PUT"])
def index(request, index_name):

	"""
		Index management
	"""

	if request.method == "GET":
		'''
		  Return info about the index.
		  Example:
		      curl -X GET  http://localhost:8000/index/
		      In which "index" is the "index_name".
		'''
		index_wrapper = IndexWrapper(index_name)

		# Return the info of ES index "index_name"
		info = index_wrapper.get_index_info()
		
		#return JSONResponse({"Message": "Request to read index " + index_name})
		return JSONResponse(info[index_name]['mappings'])
	
	elif request.method == "PUT":
		'''
		  Create the index if it does not exist
		  Example:
		      curl -X PUT  http://localhost:8000/index/index_name/
		'''
		try:
			index = Index.objects.get(name = index_name)
			print("Index name exists in the database.")
		except:
			index = Index()
			index.name = index_name
			index_wrapper = IndexWrapper(index_name)
			index.save()

		return JSONResponse({"Message": "Created index " + index_name})
	
	# Should not happen
	return Response(status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST"])
def search(request, index_name):
	result = []
	'''
	       curl -X POST http://localhost:8000/index/_search -d @queries/...
	'''
	if request.method == "POST":
		"""
		Request body should be a SearchContext object,
		which has info including: 
		search type(mandatory), search pattern(mandatory when pattern search),
		search text(optional when pattern search, mandatory when lyrics search), 
		and mirror search(optional).
		"""

		body_unicode = request.body.decode('utf-8')
		body = json.loads(body_unicode)

		print(body)
		
		searchcontext = SearchContext()
		# json -> searchcontext
		searchcontext.read(body)
		
		"""
		print the content of SearchContext object
		"""
		print("\n\nsearch type: ", searchcontext.search_type)
		if searchcontext.pattern:
			print("ABC encoded pattern: ", searchcontext.pattern)
		if searchcontext.text:
			print("text: ", searchcontext.text)
		if searchcontext.search_type != "lyrics":
			print("mirror search: ", searchcontext.mirror_search,"\n\n")

		index_wrapper = IndexWrapper(index_name)
		"""
		  The following call includes:
		  searchcontext.pattern(abc format) -> music21 objects
		  music21 objects -> items -> pattern sequence
		  sequence -> encoded n-grams according to search type
		  search in ES
		"""
		# ES returns a "response" object with all the documents that matches query
		
		# Check if index of index_name exists. 
		if Index.objects.filter(name=index_name).exists():
			print("An index with the same name already exists in the database.")

		matching_docs = index_wrapper.search(searchcontext)

		# Get a list of doc_id
		matching_doc_ids = []
		for hit in matching_docs.hits.hits:
			matching_doc_ids.append(hit['_id'])

		print("Matching documents are:", matching_doc_ids)

		# Get matching ids(positions) of patterns in MusicSummary for highlighting
		matching_locations = index_wrapper.locate_matching_patterns(index_name, matching_doc_ids, searchcontext)

		print("Locations of matching patterns are:", matching_locations)
		return JSONResponse({"Message": "Search executed in index " + index_name, "Matching locations:": matching_locations})
		
@csrf_exempt
@api_view(["GET", "PUT"])
def document(request, index_name, doc_id):

	"""
		Document management.
		GET a musicdoc refers to MusicSummary retrieval of the musicdoc.
		PUT a musicdoc refers to index an music document in ElasticSearch index, 
		given index_name, doc_id and music document.
		Specifically: id, json encoded MusicSummary, and descriptors of the musicdoc are indexed.
	"""

	if request.method == "GET":
		'''
			Example:
			    curl -X GET  http://localhost:8000/index/lklk/
		'''
		index_wrapper = IndexWrapper(index_name)

		# Return MusicSummary of the given doc_id which is indexed in ES.
		try:
			MS = index_wrapper.get_MS_from_doc(index_name, doc_id)
		except Exception as ex:
			return JSONResponse({"Error when getting the score model": str(ex)})

		# Return the corresponding MusicSummary(score model)
		return JSONResponse({"Message": "Request to read MusicSummary of " + doc_id + ":" + MS})

	elif request.method == "PUT":

		# Load, process and index the music document
		try:
			if request.content_type == "application/zip":
				"""
				Bulk process and index all music documents from a zip file.
				in the case of loading a zip, "doc_id" from the curl command is just the name of zip file.
				It would not be saved on ES as id, but the name of each file would be considered as id of it.
				Example:
				curl -X PUT -H "Content-type:application/zip" http://localhost:8000/index/testzip/ --data-binary @data/test_zip.zip
				"""
				try:
					ScoreProcessing.load_and_process_zip(index_name, request.body)
				except Exception as ex:
					return JSONResponse({"Error while loading zip": str(ex)})

				return JSONResponse({"message": "Successfully bulk indexed all documents in zip: " + doc_id})

			else:

				body_unicode = request.body.decode('utf')
				
				if request.content_type == "application/mei":
					"""
					Example:
		       		curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/lklk/ -d @data/friuli001.mei
		       		In which "index" refers to index_name, and "lklk" refers to doc_id.
		       		"""
					# Apply MEI -> Music21 converter
					m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mei", doc_id)
				
				elif request.content_type == "application/xml":
					"""
					Example:
					curl -X PUT -H "Content-type:application/xml"
					http://localhost:8000/index/couperin/ -d @data/couperin.xml
					"""
					m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "xml", doc_id)
				
				elif request.content_type == "application/musicxml" or request.content_type == "application/vnd.recordare.musicxml+xml":
					"""
					Example 1:
					curl -X PUT -H "Content-type:application/musicxml" 
					http://localhost:8000/index/testmxml/ --data-binary @data/Gas0301f.musicxml 
					Example 2: 
					curl -X PUT -H "Content-type:application/vnd.recordare.musicxml+xml" 
					http://localhost:8000/index/testmxml/ -d @data/Gas0301f.musicxml
					"""
					m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "musicxml", doc_id)

					"""
				elif request.content_type == "application/vnd.recordare.musicxml":
				
					#The recommended media type for a compressed MusicXML file(.mxl) is: application/vnd.recordare.musicxml
					
					m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mxl", doc_id)
					"""
				elif request.content_type == "application/krn":
					"""
					Kern is not registered as a content type, thus use --data-binary!
					Example:
					curl -X PUT -H "Content-type:application/krn" http://localhost:8000/index/danmark/ --data-binary @data/danmark1.krn
					"""
					m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "krn", doc_id)

				elif request.content_type == "application/abc":
					"""
					Example:
					curl -X PUT -H "Content-type:application/abc" http://localhost:8000/index/abctest/ --data-binary @data/test.abc
					"""
					m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "abc", doc_id)
				#elif request.content_type == "application/rtp-midi":
				#	m21_score, musicdoc  = ScoreProcessing.load_score(index_name, body_unicode, "midi", doc_id)
				#   Humdrum for later?
				else:
					# Otherwise, the format is not supported.
					return JSONResponse({"Error": "Not supported content type: " + request.content_type})

				# Process the current score, produce descriptors from MusicSummary
				descr_dict, encodedMS = ScoreProcessing.process_score(musicdoc, m21_score, doc_id)
				
				# Index the current musicdoc, including id, MusicSummary and descriptors
				index_wrapper = IndexWrapper(index_name) 
				index_wrapper.index_musicdoc(index_name, musicdoc, descr_dict, encodedMS)
				
				return JSONResponse({"message": "Successfully indexed document " + doc_id})
		except Exception as ex:
			return JSONResponse({"Error while loading music file": str(ex)})

	return Response(status=status.HTTP_400_BAD_REQUEST)