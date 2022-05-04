from django.shortcuts import render
from django.template import loader

from django.http import HttpResponse

from elasticsearch import Elasticsearch

from lib.search.SearchContext import *

def index(request):
    template = loader.get_template('home/index.html')
    context = {}
    return HttpResponse(template.render(context, request))


# def LoadDataView(request):
    # return HttpResponse("Load a single music score or zip, with instruction displayed")

def OverviewDataView(request):
    template = loader.get_template('home/dashboard.html')
    es = Elasticsearch()
    indices = es.indices.get_alias()
    indices_stats = {}
    for key in indices.keys():
        # stats[key] = es.indices.stats(key)
        indices_stats[key] = es.indices.stats(key).get('_all').get('primaries').get('docs').get('count')

    context = {"indices_number": len(indices_stats), "indices_stats": indices_stats}
    return HttpResponse(template.render(context, request))

def MusicDocView(request):
    return HttpResponse("Display music doc without search result")

# def SearchView(request):
    # return HttpResponse("Search with keyboard, abc text etc")

# """
# def MainView(request):
    # return HttpResponse("A combo of SearchView and LoadDataView?")
# """
# def SearchResultView(request):
    # return HttpResponse("Display search result and perhaps kibana analysis")

# def HighlightMusicDocView(request):
    # return HttpResponse("Display music doc with highlighted search result")
