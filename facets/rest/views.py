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
from elasticsearch import Elasticsearch

# Get an instance of a logger
logger = logging.getLogger(__name__)

def establish_es_connection():
	try:
		# host = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"]
		hp = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"][0]
		host=hp["host"]
		port=hp["port"]
		es = Elasticsearch(hosts=[ {'host': host, 'port': port}, ])
	except:
		print("\n\n**rest**** Error connecting to Elasticsearch, please check your if it is running.")
    return es

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
              curl -X GET  http://localhost:8000/index/index_name/
        '''

        es = establish_es_connection()
        esindices = es.indices.get_alias()
        if index_name in esindices:
            index_wrapper = IndexWrapper(index_name)
            # Read the info on ES index "index_name"
            info = index_wrapper.get_index_info()
            return JSONResponse(info[index_name]['mappings'])
        else:
            return JSONResponse({"This index does not exist on ES."})
    
    elif request.method == "PUT":
        '''
          Create the index if it does not exist.

          Example:
              curl -X PUT  http://localhost:8000/index/index_name/
        '''
        try:
            es = establish_es_connection()
            indices = es.indices.get_alias()
        except Exception as ex:
            return JSONResponse({"Elasticsearch is not connected:" + ex})

        if index_name in indices:
            return JSONResponse({"Message": "Index already exists in ES:" + index_name})
        else:
            # Create index on ES
            index_wrapper = IndexWrapper(index_name)

            # If it does not exist on ES but exists in database, it should be erased from database first
            if Index.objects.filter(name=index_name).exists():
                Index.objects.filter(name=index_name).delete()

            # Save in the database
            index = Index()
            index.name = index_name
            index.save()

            return JSONResponse({"Message": "Created index " + index_name})
    """
    elif request.method == "DELETE":
        print(index_name)
        if index_name == "scorelib":
            return JSONResponse({"Message": "Not allowed to delete" + index_name})
    """

    # Should not happen
    return Response(status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST"])
def search(request, index_name):
    result = []
    '''
        Example:
        curl -X POST http://localhost:8000/index/index_name/_search -d @queries/...
    '''
    if request.method == "POST":

        """
        Request body should be a SearchContext object,
        which has info including: 
        search type(mandatory), search pattern(mandatory when pattern search),
        search text(optional when pattern search, mandatory when lyrics search), 
        and mirror search(optional).
        """
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
        except Exception as ex:
            return JSONResponse({"Error when loading json, check if it exists": str(ex)})
        
        searchcontext = SearchContext()
        # json -> searchcontext
        try:
            searchcontext.read(body)
        except Exception as ex:
            return JSONResponse({"Error when reading json, check if search type and index name are specified": str(ex)})
        
        """
        Print the content of SearchContext object
        """
        print("\n\nsearch type: ", searchcontext.search_type)
        if searchcontext.pattern:
            print("ABC encoded pattern: ", searchcontext.pattern)
        if searchcontext.text:
            print("text: ", searchcontext.text)
        if searchcontext.search_type != "lyrics":
            print("mirror search: ", searchcontext.mirror_search,"\n\n")
        # If use curl to send search request, facet related filters should be specified in json
        if searchcontext.facet_composers != []:
            print("Faceted: search for work composed by:")
            for composer in searchcontext.facet_composers:
                print(composer)

        if not searchcontext.check_pattern_length():
            searchcontext.pattern = ""
            if searchcontext.keywords != "":
                print("Pattern not valid, we are in keyword search mode.")
            else:
                return JSONResponse({"Message": "Can not execute the search, please re-enter a valid pattern: it must contain at least three intervals"})

        # Check if index of index_name exists on ES.
        
        es = establish_es_connection()
        indices = es.indices.get_alias()
        if index_name not in indices:
            return JSONResponse({"Message": "Can not execute the search, index does not exist " + index_name})
        # The following checks the database, but not needed if checked in ES
        #if Index.objects.filter(name=index_name).exists():
        #    print("An index with the same name already exists in the database.")

        index_wrapper = IndexWrapper(index_name)
        """
          The following call does:
          searchcontext.pattern(abc format) -> music21 objects
          music21 objects -> items -> pattern sequence
          sequence -> encoded n-grams according to search type
          search in ES
        """
        # ES returns a "response" object with all the documents that matches query


        # Make sure the composer(s) specified exists in index:
        if searchcontext.facet_composers != []:
            composer_names = index_wrapper.get_all_composer_names()
            for cur_composer in searchcontext.facet_composers:
                if cur_composer not in composer_names:
                    return JSONResponse({"Message": "Can not execute the search, composer does not exist " + cur_composer})

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
        try:
            #es = Elasticsearch(hosts=[{'host': settings.ELASTIC_SEARCH["host"], 'port': settings.ELASTIC_SEARCH["port"]}],)
            es = establish_es_connection()
        except:
            return JSONResponse({"Error connecting to Elasticsearch, please check your connection."})
        
        indices = es.indices.get_alias()
        
        # First check if the index exists on ES
        if index_name in indices:
            index_wrapper = IndexWrapper(index_name)
            # Then return MusicSummary of the given doc_id which is indexed in ES.
            try:
                # TODO: should we check if this musicdoc exists in this index?
                MS = index_wrapper.get_MS_from_doc(index_name, doc_id)
            except Exception as ex:
                return JSONResponse({"Error when getting the score information from ES.": str(ex)})
        else:
            return JSONResponse("The required index does not exist on ES, please create a new index or query an existing index.")

        # Return the corresponding MusicSummary(score model)
        return JSONResponse({"Message": "Read MusicSummary of " + doc_id + ":" + MS})

    elif request.method == "PUT":
        try:
                es = establish_es_connection()
                #es = Elasticsearch(hosts=[{'host': settings.ELASTIC_SEARCH["host"], 'port': settings.ELASTIC_SEARCH["port"]}],)
        except:
                return JSONResponse({"Error connecting to Elasticsearch, please check your connection."})
        
        indices = es.indices.get_alias()
        
        # First check if the index exists on ES
        if index_name not in indices:
                return JSONResponse({"Message": "The index does not exist, please create a new index or change the name to an existing one."})


        # Load, process and index the music document
        try:
            if request.content_type == "application/zip":
                """
                Bulk process and index all music documents from a zip file.
                in the case of loading a zip, "doc_id" from the curl command is just the name of zip file.
                It would not be saved on ES as id, but the name of each file would be considered as id of it.

                Example:
                curl -X PUT -H "Content-type:application/zip" http://localhost:8000/index/index_name/testzip/ --data-binary @data/test_zip.zip

                """
                #try:
                flag = ScoreProcessing.load_and_process_zip(index_name, request.body)
                #except Exception as ex:
                #    return JSONResponse({"Error while loading zip": str(ex)})
                if flag == True:
                    return JSONResponse({"message": "Error when loading zip: no valid document found."})

                return JSONResponse({"message": "Successfully bulk indexed all documents in zip: " + doc_id})

            else:

                if request.content_type != "application/midi":
                    # Avoid using utf to decode midi, it causes error
                    body_unicode = request.body.decode('utf')
                
                if request.content_type == "application/mei":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/index_name/lklk/ -d @data/friuli001.mei
                    
                    In which "index" refers to index_name, and "lklk" refers to doc_id.
                    """
                    # Apply MEI -> Music21 converter
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mei", doc_id)

                    if m21_score == "" and musicdoc == None:
                        return JSONResponse({"Error": "Error when reading MEI file: "+doc_id})
                
                elif request.content_type == "application/xml":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/xml"
                    http://localhost:8000/index/index_name/couperin/ -d @data/couperin.xml
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "xml", doc_id)
                    if m21_score == "" and musicdoc == None:
                        return JSONResponse({"Error": "Error when reading XML file: "+doc_id})
                
                elif request.content_type == "application/musicxml" or request.content_type == "application/vnd.recordare.musicxml+xml":
                    """
                    Example 1:
                    curl -X PUT -H "Content-type:application/musicxml" 
                    http://localhost:8000/index/index_name/testmxml/ --data-binary @data/Gas0301f.musicxml 

                    Example 2: 
                    curl -X PUT -H "Content-type:application/vnd.recordare.musicxml+xml" 
                    http://localhost:8000/index/index_name/testmxml/ -d @data/Gas0301f.musicxml

                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "musicxml", doc_id)
                    if m21_score == "" and musicdoc == None:
                        return JSONResponse({"Error": "Error when reading MusicXML file: "+doc_id})

                    """
                elif request.content_type == "application/vnd.recordare.musicxml":
                
                    #The recommended media type for a compressed MusicXML file(.mxl) is: application/vnd.recordare.musicxml
                    
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mxl", doc_id)
                    """
                elif request.content_type == "application/krn":
                    """
                    # Kern is not registered as a content type, thus use --data-binary!

                    Example:
                    curl -X PUT -H "Content-type:application/krn" http://localhost:8000/index/index_name/danmark/ --data-binary @data/danmark1.krn
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "krn", doc_id)
                    if m21_score == "" and musicdoc == None:
                        return JSONResponse({"Error": "Error when reading HUMDRUM file: "+doc_id})

                elif request.content_type == "application/abc":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/abc" http://localhost:8000/index/index_name/abctest/ --data-binary @data/test.abc
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "abc", doc_id)
                    if m21_score == "" and musicdoc == None:
                        return JSONResponse({"Error": "Error when reading ABC file: "+doc_id})

                elif request.content_type == "application/midi":
                    """
    
                    Example:
                    curl -X PUT -H "Content-type:application/midi" http://localhost:8000/index/index_name/miditest/ --data-binary @data/mazurka06-1.mid
                    """
                    return JSONResponse({"Message": "MIDI format is not supported yet"})

                    # To be fixed: why the intervals are 20D etc.?
                    #m21_score, musicdoc  = ScoreProcessing.load_score(index_name, request.body, "mid", doc_id)
                    #if m21_score == "" and musicdoc == None:
                    #    return JSONResponse({"Error": "Error when reading MIDI file: "+doc_id})
                else:
                    # Otherwise, the format is not supported.
                    return JSONResponse({"Error": "Not supported content type: " + request.content_type})

                # Process the current score, produce descriptors from MusicSummary
                descr_dict, encodedMS, extracted_infos = ScoreProcessing.process_score(musicdoc, m21_score, doc_id)
                
                # Index the current musicdoc, including id, MusicSummary and descriptors
                index_wrapper = IndexWrapper(index_name) 
                index_wrapper.index_musicdoc(index_name, musicdoc, descr_dict, encodedMS, extracted_infos)
                
                return JSONResponse({"message": "Successfully indexed document " + doc_id})
        except Exception as ex:
            return JSONResponse({"Error while loading music file": str(ex)})

    return Response(status=status.HTTP_400_BAD_REQUEST)
