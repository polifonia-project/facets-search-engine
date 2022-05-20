from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader

from lib.process import ScoreProcessing
from lib.search.IndexWrapper import IndexWrapper

from elasticsearch import Elasticsearch
from django.conf import settings

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[
        {'host': host, 'port': settings.ELASTIC_SEARCH["port"]},
        {'host': "FACETS-ES", 'port': 9200},
        {'host': "0.0.0.0", 'port': 9200}
    ])
except:
    print("\n\n******Error connecting to Elasticsearch, please check your if it is running.")


def loaddataIndex(request):
    template = loader.get_template('loaddata/index.html')
    indices = es.indices.get_alias().keys()
    context = {"indices_names": indices}
    return HttpResponse(template.render(context, request))

def uploaddata(request, index_name, doc_id):

    if request.method == "PUT":

        # Load, process and index the music document
        try:

            #uploadrequest["indexname"] = request.PUT.get('indexname')
            #uploadrequest["filename"] = request.PUT.get('filename')
            
            if request.content_type == "application/zip":
                """
                Bulk process and index all music documents from a zip file.
                in the case of loading a zip, "doc_id" from the curl command is just the name of zip file.
                It would not be saved on ES as id, but the name of each file would be considered as id of it.

                Example:
                curl -X PUT -H "Content-type:application/zip" http://localhost:8000/index/index_name/testzip/ --data-binary @data/test_zip.zip

                """
                try:
                    ScoreProcessing.load_and_process_zip(index_name, request.body)
                except Exception as ex:
                    return HTTPResponse({"Error while loading zip": str(ex)})
                #TODO: template = ??
                context = {"zip_id": doc_id}
                #return HttpResponse(template.render(context, request))
                return HTTPResponse({"Successfully bulk indexed zip:": doc_id})
                #TODO: then redirect to dashboard/upload page?
                #return HttpResponseRedirect('dashboard/')
            else:

                if request.content_type != "application/midi":
                    # Avoid using utf to decode midi, it causes error
                    body_unicode = request.body.decode('utf')
                else:
                    return HTTPResponse("MIDI format is not supported yet, coming soon!")
                
                if request.content_type == "application/mei":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/index_name/lklk/ -d @data/friuli001.mei
                    In which "index" refers to index_name, and "lklk" refers to doc_id.
                    """
                    # Apply MEI -> Music21 converter
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mei", doc_id)
                
                elif request.content_type == "application/xml":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/xml"
                    http://localhost:8000/index/index_name/couperin/ -d @data/couperin.xml
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "xml", doc_id)
                
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

                    """
                elif request.content_type == "application/vnd.recordare.musicxml":
                
                    #The recommended media type for a compressed MusicXML file(.mxl) is: application/vnd.recordare.musicxml
                    
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mxl", doc_id)
                    """
                elif request.content_type == "application/krn":
                    """
                    Kern is not registered as a content type, thus use --data-binary!
                    Example:
                    curl -X PUT -H "Content-type:application/krn" http://localhost:8000/index/index_name/danmark/ --data-binary @data/danmark1.krn
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "krn", doc_id)

                elif request.content_type == "application/abc":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/abc" http://localhost:8000/index/index_name/abctest/ --data-binary @data/test.abc
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "abc", doc_id)
                else:
                    # Otherwise, the format is not supported.
                    return HttpResponse({"Error": "Not supported content type: " + request.content_type})

                # Process the current score, produce descriptors from MusicSummary
                descr_dict, encodedMS = ScoreProcessing.process_score(musicdoc, m21_score, doc_id)
                
                # Index the current musicdoc, including id, MusicSummary and descriptors
                index_wrapper = IndexWrapper(index_name) 
                index_wrapper.index_musicdoc(index_name, musicdoc, descr_dict, encodedMS)
                
                # TO-DO: Need to create a new template???
                #template = loader.get_template('loaddata/???.html') 
                context = {"musicdoc": musicdoc, "descr_dict": descr_dict, "encodedMS": encodedMS}
                #return HttpResponse(template.render(context, request))
                return HttpResponse({"Successfully indexed music document:": doc_id})

        except Exception as ex:
            return HTTPResponse({"Error while loading music file": str(ex)})
