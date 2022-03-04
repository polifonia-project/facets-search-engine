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

from music21 import converter, mei

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

		# return the info about ES index "index_name"
		info = index_wrapper.get_index_info(index_name)
		
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

		searchcontext = SearchContext()
		searchcontext.read(body)
		
		"""
		print the content of SearchContext object
		"""
		print("\n\nsearch type: ", searchcontext.search_type)
		print("pattern: ", searchcontext.pattern)
		print("text: ", searchcontext.text)
		print("mirror search: ", searchcontext.mirror_search,"\n\n")

		searchcontext.decode_pattern_context()

	return JSONResponse({"Message": "Search executed in index " + index_name})
	#return JSONResponse({"Message": "Search executed in index " + index_name, "Result": result})

@csrf_exempt
@api_view(["GET", "PUT"])
def document(request, index_name, doc_id):

	"""
		Document management
	"""

	if request.method == "GET":
		'''
			Example:
			    curl -X GET  http://localhost:8000/index/lklk/
		'''
		index_wrapper = IndexWrapper(index_name)

		#TODO: get doc info
		#docinfo = index_wrapper.get_doc_info(index_name, doc_id)
		#send a match_all query and only get the doc names
		#return JSONResponse(docinfo)

		return JSONResponse({"Message": "Request to read document " + doc_id})

	elif request.method == "PUT":
		'''
		   Example:
		       curl -X PUT -H "Content-type: application/mei" http://localhost:8000/index/lklk/ -d @data/friuli001.mei 
		       
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
				musicdoc, descr_dict = ScoreProcessing.score_process(m21_score, doc_id)
				
				#Index the current musicdoc and its descriptors in the index named "index_name"
				index_wrapper = IndexWrapper(index_name) 
				index_wrapper.index_musicdoc(index_name, musicdoc, descr_dict)
				
				return JSONResponse({"message": "Successfully indexed MEI document " + doc_id})
			else:
				return JSONResponse({"error": "Unknown content type : " + request.content_type})

		except Exception as ex:
			return JSONResponse({"error": str(ex)})


	return Response(status=status.HTTP_400_BAD_REQUEST)
