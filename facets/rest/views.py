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

from lib.process import ScoreProcessing

from lib.search.IndexWrapper import IndexWrapper

from lib.search.SearchContext import *

from lib.music.MusicSummary import *
from music21 import converter, mei


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

		# return the info about ES index "index_name"
		info = index_wrapper.get_index_info()
		
		#return JSONResponse({"Message": "Request to read index " + index_name})
		return JSONResponse(info[index_name]['mappings'])
	
	elif request.method == "PUT":
		'''
		  Create the index if it does not exist
		  Example:
		      curl -X PUT  http://localhost:8000/index/
		'''
		index_wrapper = IndexWrapper(index_name)

		return JSONResponse({"Message": "Request to create index " + index_name})
	
	# Should not happen
	return Response(status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST"])
def search(request, index_name):
	result = []
	'''
	       curl -X POST http://localhost:8000/index/_search -d @json_path
	'''
	if request.method == "POST":
		#check if index_name exists
		#Request body should be a SearchContext object,
		#which has info including: search type, search attern, search text,
		#and mirror search.

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

		"GET" a musicdoc refers to MusicSummary retrieval of the musicdoc, given its id.

		"PUT" a musicdoc refers to index an music document in ElasticSearch index, given the index name, musicdoc id and music document.

		The indexed information of a musicdoc are its id, json encoded MusicSummary, and descriptors.

	"""

	if request.method == "GET":
		'''
			Example:
			    curl -X GET  http://localhost:8000/index/lklk/
		'''
		index_wrapper = IndexWrapper(index_name)

		# Return MusicSummary of the given doc_id which is indexed in ES.

		MS = index_wrapper.get_MS_from_doc(index_name, doc_id)

		print("MusicSummary of ", doc_id, "is", MS)

		return JSONResponse({"Message": "Request to read MusicSummary of " + doc_id + ":" + MS})

	elif request.method == "PUT":
		'''
		    Example:
		       curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/lklk/ -d @data/friuli001.mei 
		       
		       In which "index" refers to index_name, and "lklk" refers to doc_id.
		'''
		# Read the document
		try:
			if request.content_type == "application/mei":
				# Apply the MEI -> Music21 converter
				conv = mei.MeiToM21Converter(request.body)

				# Get M21 object of the score
				m21_score = conv.run()

				# Process the current score, produce descriptors from MusicSummary
				musicdoc, descr_dict, encodedMS = ScoreProcessing.score_process(m21_score, doc_id)
				
				# Index the current musicdoc, including id, musicsummary and its descriptors in "index_name" index
				index_wrapper = IndexWrapper(index_name) 
				index_wrapper.index_musicdoc(index_name, musicdoc, descr_dict, encodedMS)
				
				return JSONResponse({"message": "Successfully indexed MEI document " + doc_id})
			else:
				# TODO: bulk indexing given a zip file

				return JSONResponse({"error": "Unknown content type : " + request.content_type})

		except Exception as ex:
			return JSONResponse({"error": str(ex)})


	return Response(status=status.HTTP_400_BAD_REQUEST)
