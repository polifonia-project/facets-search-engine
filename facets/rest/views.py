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
		return JSONResponse({"Message": "Request to read index " + index_name})
	elif request.method == "PUT":
		return JSONResponse({"Message": "Request to create index " + index_name})
	
	# Should not happen
	return Response(status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(["GET", "PUT"])
def index(request, index_name):

	"""
		Index management
	"""

	if request.method == "GET":
		'''
		  To do: return some info on the index
		'''
		return JSONResponse({"Message": "Request to read index " + index_name})
	
	elif request.method == "PUT":
		'''
		  To do: create the index if it does not exist
		'''
		return JSONResponse({"Message": "Request to create index " + index_name})
	
	# Should not happen
	return Response(status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["GET", "PUT"])
def document(request, index_name, doc_id):

	"""
		Document management
	"""

	if request.method == "GET":
		return JSONResponse({"Message": "Request to read document " + doc_id})
	elif request.method == "PUT":
		'''
		   Example=
		     curl -X PUT -H "Content-type: application/mei" http://localhost:8000/index/lklk/ -d @data/friuli001.mei 
		'''
		# Read the document
		try:
			if request.content_type == "application/mei":
				# Apply the MEI -> Music21 converter
				conv = mei.MeiToM21Converter(request.body)
				# Get M21 object of the score
				m21_score = conv.run()

				# Process current score
				ScoreProcessing.score_process(m21_score)

				# index it

				return JSONResponse({"message": "Request to create MEI document " + doc_id})
			else:
				return JSONResponse({"error": "Unknown content type : " + request.content_type})

		except Exception as ex:
			return JSONResponse({"error": str(ex)})
	
	# Should not happen
	return Response(status=status.HTTP_400_BAD_REQUEST)

