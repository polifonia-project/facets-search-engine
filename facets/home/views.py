from django.shortcuts import render
from django.template import loader
from django.conf import settings
from pprint import pprint
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework import renderers
#from rest_framework.renderers import JSONRenderer
#from rest_framework.parsers import JSONParser
import json

from elasticsearch import Elasticsearch

from lib.search.IndexWrapper import IndexWrapper

from rest.models import *

class AboutView(TemplateView):
    template_name = "home/about.html"

class DocsView(TemplateView):
    template_name = "home/docs.html"

try:
    # host = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"]
    hp = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"][0]
    host=hp["host"]
    port=hp["port"]
    es = Elasticsearch(hosts=[ {'host': host, 'port': port}, ])
except:
    print("\n\n**home**** Error connecting to Elasticsearch, please check your if it is running.")


def index(request):
    template = loader.get_template('home/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

def fetch_musicdoc(request, index_name, doc_id):

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

# Dashboard
def OverviewDataView(request):
    template = loader.get_template('home/dashboard.html')
    try:
        indices = es.indices.get_alias()
    except:
        # if ES is not connected, it should be warned
        template = loader.get_template('home/es_errorpage.html')
        context = {}
        return HttpResponse(template.render(context, request))
    
    indices_stats = {}
    for key in indices.keys():
        # stats[key] = es.indices.stats(key)
        indices_stats[key] = es.indices.stats(key).get('_all').get('primaries').get('docs').get('count')

    context = {"indices_number": len(indices_stats), "indices_stats": indices_stats}
    return HttpResponse(template.render(context, request))

# View index by name
def IndexView(request, index_name):

    if request.method == "GET":
        # Return the info of ES index "index_name".
        template = loader.get_template('home/indexview.html')

        try:
            indices = es.indices.get_alias()
        except:
            # if ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if index_name in indices:
            info = {}
            info["docs_number"] = es.indices.stats(index_name).get('_all').get('primaries').get('docs').get('count')
            
            doc_results = {}
            # Here we run a query to retrieve some ids
            # important: size is 1000 for now, to adjust put a new number it in settings.
            res = es.search(index=index_name, body={"query": {"match_all": {}}}, size = settings.MAX_ITEMS_IN_RESULT)

            for hit in res['hits']['hits']:
                doc_results[hit["_id"]] = {}
                doc_results[hit["_id"]]["source"] = hit["_source"]

            request.session["doc_results"] = doc_results

            print(len(doc_results))

            p = Paginator(tuple(doc_results), settings.ITEMS_PER_PAGE)
            #the number of items to display in total: #print(p.count)
            print(p.num_pages)

            callpage = request.GET.get('page', False)
            if callpage != False:
                try:
                    pg = p.get_page(callpage)
                except PageNotAnInteger:
                    pg = p.get_page(1)
                except EmptyPage:
                    pg = p.get_page(p.num_pages)
            else:
                pg = p.get_page(1)

            context = {"index_name": index_name, "info": info, "documents": doc_results, "pg":pg}
        else:
            return HttpResponse("This index does not exist on ES.")
    
    return HttpResponse(template.render(context, request))

def MusicDocView(request, index_name, doc_id):
    template = loader.get_template('home/musicdocview.html')

    try:
        musicdoc = MusicDoc.objects.get(doc_id=doc_id)
    except Exception as ex:
        return HttpResponse("No music document found in database.")
    try:
        # just to make sure it is stored and there is a path
        if musicdoc.doc_type == 'krn':
            doc_path = musicdoc.krnfile.path #.path is the absolute path, not url
            # Use verovio-humdrum kit
        elif musicdoc.doc_type == 'musicxml':
            doc_path = musicdoc.musicxmlfile.path
        elif musicdoc.doc_type == 'mei':
            doc_path = musicdoc.meifile.path
        elif musicdoc.doc_type == 'xml':
            # does verovio support xml? 
            doc_path = musicdoc.xmlfile.path
        elif musicdoc.doc_type == 'abc':
            # does verovio support abc? 
            doc_path = musicdoc.abcfile.path
        if doc_path == None:
            return HttpResponse("No path found for document fetching.")
    
        # get the url to display score
        hostname = request.get_host()
        doc_url = "http://"+hostname+ "/home/media/"+index_name+"/"+doc_id+"/"

        # get metadata info from database
        if musicdoc.title:
            md_title = musicdoc.title
        else:
            md_title = "Unknown Title"
        if musicdoc.composer:
            md_composer = musicdoc.composer
        else:
            md_composer = "Unknown Composer"

    except Exception as ex:
        return HttpResponse("Error while retrieving file from database to display: "+ str(ex))

    context = {
        "index_name": index_name,
        "doc_type": musicdoc.doc_type,
        "doc_id": doc_id,
        "doc_url": doc_url,
        "doc_title": md_title,
        "doc_composer": md_composer
        }
    return HttpResponse(template.render(context, request))
