from django.shortcuts import render
from django.template import loader
from django.conf import settings
from pprint import pprint

from django.http import HttpResponse

from elasticsearch import Elasticsearch

from lib.search.IndexWrapper import IndexWrapper

from rest.models import *

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[
        {'host': host, 'port': settings.ELASTIC_SEARCH["port"]},
        {'host': "FACETS-ES", 'port': 9200},
        {'host': "0.0.0.0", 'port': 9200}
    ])
except:
    print("\n\n******Error connecting to Elasticsearch, please check your if it is running.")

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

def fetch_musicdoc(request, index_name, doc_id):

    #template = loader.get_template('home/fetchmusicdoc.html')
    try:
        musicdoc = MusicDoc.objects.get(doc_id=doc_id)
    except Exception as ex:
        return HttpResponse("No music document found in database.")
    try:
        if musicdoc.doc_type == 'krn':
            doc = musicdoc.krnfile #.path is the absolute path, not url
            # Use verovio-humdrum kit
        elif musicdoc.doc_type == 'musicxml':
            doc = musicdoc.musicxmlfile
        elif musicdoc.doc_type == 'mei':
            doc = musicdoc.meifile
        elif musicdoc.doc_type == 'xml':
            # does verovio support xml? 
            doc = musicdoc.xmlfile
        elif musicdoc.doc_type == 'abc':
            # does verovio support abc? 
            doc = musicdoc.abcfile
    except Exception as ex:
        return HttpResponse("Error while fetching file from database: "+ str(ex))

    if doc.url == None:
        return HttpResponse("No path found for document display.")

    return HttpResponse(doc)

    #context = {"doc_id": doc_id, "doc_url": doc.url}
    #return HttpResponse(template.render(context, request))

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
            # info = {"aa" : 2, "bb": 3}
            info = {}
            info["docs_number"] = es.indices.stats(index_name).get('_all').get('primaries').get('docs').get('count')
            doc_results = {}
            # print(es.indices.stats(index_name).get('_all').get('primaries').get('docs'))
            # here we need to run a query to retrieve some ids
            res = es.search(index=index_name, body={"query": {"match_all": {}}},
                            size = 30)
            # print("----- Got %d Hits:" % res['hits']['total']['value'])
            for hit in res['hits']['hits']:
                doc_results[hit["_id"]] = {}
                doc_results[hit["_id"]]["source"] = hit["_source"]
                # doc_results[hit["_id"]]["path"] = hit["_source"]
                # make a check here for the keys to display
                # print("%(corpus_ref)s %(ref)s: %(composer)s - %(title)s" % hit["_source"])
                # print(hit["_source"])

            context = {"index_name": index_name, "info": info, "documents": doc_results}
        else:
            return HttpResponse("This index does not exist on ES.")
    
    return HttpResponse(template.render(context, request))

def MusicDocView(request, index_name, doc_id):
    template = loader.get_template('home/musicdocview.html')
    # this "verovio_test.html" template is for testing only!!
    # template = loader.get_template('home/verovio_test.html')

    try:
        musicdoc = MusicDoc.objects.get(doc_id=doc_id)
        #MusicDoc.objects.filter(doc_id=docid)
    except Exception as ex:
        return HttpResponse("No music document found in database.")
    try:
        print("------\n")
        pprint(vars(musicdoc.meifile))
        print("------\n")
        if musicdoc.doc_type == 'krn':
            doc_url = musicdoc.krnfile.url #.path is the absolute path, not url
            # Use verovio-humdrum kit
        elif musicdoc.doc_type == 'musicxml':
            doc_url = musicdoc.musicxmlfile.url
        elif musicdoc.doc_type == 'mei':
            doc_url = musicdoc.meifile.url
        elif musicdoc.doc_type == 'xml':
            # does verovio support xml? 
            doc_url = musicdoc.xmlfile.url
        elif musicdoc.doc_type == 'abc':
            # does verovio support abc? 
            doc_url = musicdoc.abcfile.url
    except Exception as ex:
        return HttpResponse("Error while retrieving file from database to display: "+ str(ex))

    if doc_url == None:
        return HttpResponse("No path found for document display.")

    context = {"index_name": index_name, "doc_id": doc_id, "doc_url": doc_url}
    return HttpResponse(template.render(context, request))
