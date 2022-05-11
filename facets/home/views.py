from django.shortcuts import render
from django.template import loader
from django.conf import settings

from django.http import HttpResponse

from elasticsearch import Elasticsearch

from rest.models import *

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[{'host': host, 'port': 9200}],)
except:
    print("Error connecting to ES")
    # es = Elasticsearch(hosts=[{'host': "MuSEEK-ES", 'port': 9200}],)

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

def MusicDocView(request, index_name, doc_id):
    template = loader.get_template('home/musicdocview.html')
    try:
        musicdoc = MusicDoc.objects.get(doc_id = doc_id)
    except Exception as ex:
        return HttpResponse("No music document found in database.")
    try:
        if musicdoc.doc_type == 'krn':
            doc_url = musicdoc.krnfile.path
            # But verovio does not support kern?
        elif musicdoc.doc_type == 'musicxml':
            doc_url = musicdoc.musicxmlfile.path
        elif musicdoc.doc_type == 'mei':
            doc_url = musicdoc.meifile.path
        elif musicdoc.doc_type == 'xml':
            # does verovio support xml? if not music21->musicxml->mei
            doc_url = musicdoc.xmlfile.path
        elif musicdoc.doc_type == 'abc':
            # does verovio support abc? if not music21->musicxml->mei
            doc_url = musicdoc.abcfile.path
    except Exception as ex:
        return HttpResponse("Error while retrieving file from database to display: "+ str(ex))

    if doc_url == None:
        return HttpResponse("No path found for document display.")
    context = {"index_name": index_name, "doc_id": doc_id, "doc_url": doc_url}
    return HttpResponse(template.render(context, request))


# def HighlightMusicDocView(request):
    # return HttpResponse("Display music doc with highlighted search result")

# def SearchView(request):
    # return HttpResponse("Search with keyboard, abc text etc")

# """
# def MainView(request):
    # return HttpResponse("A combo of SearchView and LoadDataView?")
# """
# def SearchResultView(request):
    # TODO: maybe this should be only in search/views.py
    # return HttpResponse("Display search result and perhaps kibana analysis")


