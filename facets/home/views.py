from django.shortcuts import render
from django.template import loader
from django.conf import settings

from django.http import HttpResponse

from elasticsearch import Elasticsearch

from lib.search.IndexWrapper import IndexWrapper

from rest.models import *

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[{'host': host, 'port': settings.ELASTIC_SEARCH["port"]}],)
except:
    try:
        print("Re-attempt to connect with different attributes. Host: MuSEEK-ES / Port: 9200\n")
        es = Elasticsearch(hosts=[{'host': "MuSEEK-ES", 'port': 9200}],)
    except:
        print("Error connecting to Elasticsearch, please check your if it is running.")

def index(request):
    template = loader.get_template('home/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

def docs(request):
    template = loader.get_template('home/docs.html')
    context = {}
    return HttpResponse(template.render(context, request))

# def LoadDataView(request):
    # return HttpResponse("Load a single music score or zip, with instruction displayed")

# dashboard
def OverviewDataView(request):
    template = loader.get_template('home/dashboard.html')
    indices = es.indices.get_alias()
    indices_stats = {}
    for key in indices.keys():
        # stats[key] = es.indices.stats(key)
        indices_stats[key] = es.indices.stats(key).get('_all').get('primaries').get('docs').get('count')

    context = {"indices_number": len(indices_stats), "indices_stats": indices_stats}
    return HttpResponse(template.render(context, request))

def IndexView(request, index_name):
    if request.method == "GET":
        # Return the info of ES index "index_name".
        template = loader.get_template('home/indexview.html')

        indices = es.indices.get_alias()
        if index_name in indices:
            # TODO: info should be a list of documents under this index!! Not just document number.
            info = es.indices.stats(index_name).get('_all').get('primaries').get('docs').get('count')
            context = {"index_name": index_name, "information": info}
        else:
            return HttpResponse("This index does not exist on ES.")
    
    return HttpResponse(template.render(context, request))

def MusicDocView(request, index_name, doc_id):
    #template = loader.get_template('home/musicdocview.html')
    # this "verovio_test.html" template is for testing only!!
    template = loader.get_template('home/verovio_test.html')
    try:
        musicdoc = MusicDoc.objects.get(doc_id = doc_id)
    except Exception as ex:
        return HttpResponse("No music document found in database.")
    try:
        if musicdoc.doc_type == 'krn':
            doc_url = musicdoc.krnfile.path
            # Use verovio-humdrum kit
        elif musicdoc.doc_type == 'musicxml':
            doc_url = musicdoc.musicxmlfile.path
        elif musicdoc.doc_type == 'mei':
            doc_url = musicdoc.meifile.path
        elif musicdoc.doc_type == 'xml':
            # does verovio support xml? 
            doc_url = musicdoc.xmlfile.path
        elif musicdoc.doc_type == 'abc':
            # does verovio support abc? 
            doc_url = musicdoc.abcfile.path
    except Exception as ex:
        return HttpResponse("Error while retrieving file from database to display: "+ str(ex))

    if doc_url == None:
        return HttpResponse("No path found for document display.")
    context = {"index_name": index_name, "doc_id": doc_id, "doc_url": doc_url}
    return HttpResponse(template.render(context, request))

