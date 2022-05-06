from django.shortcuts import render
from django.template import loader
from django.conf import settings

from django.http import HttpResponse

from elasticsearch import Elasticsearch

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[{'host': host, 'port': 9200}],)
except:
    print("error connecting to ES")
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
