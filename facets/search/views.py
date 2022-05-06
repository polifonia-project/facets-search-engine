from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
import json

from elasticsearch import Elasticsearch

from lib.process import ScoreProcessing
from lib.search.IndexWrapper import IndexWrapper
from lib.search.SearchContext import *

from elasticsearch import Elasticsearch

# Create your views here.
# es = Elasticsearch()
es = Elasticsearch(hosts=[{'host': "MuSEEK-ES", 'port': 9200}],)

def index(request):
    indices = es.indices.get_alias().keys()
    context = {"indices_names": indices}

    template = loader.get_template('search/index.html')
    return HttpResponse(template.render(context, request))

@csrf_exempt
def results(request):
    # print("result view called")
    matching_doc_ids = {}
    indices = es.indices.get_alias().keys()

    if request.method == 'POST':
        try:
            searchinput = {}
            searchinput["pattern"] = request.POST.get('pattern', False)
            if request.POST.get('mirror', False):
                searchinput["mirror"] = True
            else:
                searchinput["mirror"] = False
            searchinput["type"] = request.POST.get('searchtype', False)
            searchinput["index_name"] = request.POST.get('indexname', False)
            if searchinput["pattern"]:
                print(searchinput)
                searchcontext = SearchContext()
                # json -> searchcontext
                searchcontext.read(searchinput)
                # print the content of SearchContext object
                print("\n\nsearch type: ", searchcontext.search_type)
                if searchcontext.pattern:
                    print("ABC encoded pattern: ", searchcontext.pattern)
                if searchcontext.text:
                    print("text: ", searchcontext.text)
                if searchcontext.search_type != "lyrics":
                    print("mirror search: ", searchcontext.mirror_search,"\n\n")

                index_wrapper = IndexWrapper(searchinput["index_name"])
                # ES returns a "response" object with all the documents that matches query
                matching_docs = index_wrapper.search(searchcontext)

                # Get a list of doc_id
                matching_doc_ids = {}
                for hit in matching_docs.hits.hits:
                    doc_name = hit['_id']
                    matching_doc_ids[doc_name] = "dummy"

                #HIGHLIGHTING TODO
                # Get matching ids(positions) of patterns in MusicSummary for highlighting
                #matching_locations = index_wrapper.locate_matching_patterns(index_name, matching_doc_ids, searchcontext)
                ###matching_locations["num_occu"]

                print("Matching documents are:", matching_doc_ids)
        except:
            print("Error occurred while searching on ES index")

    template = loader.get_template('search/results.html')
    context = {
        "searchinput": searchinput,
        "results": matching_doc_ids,
        "indices_names": indices}
    return HttpResponse(template.render(context, request))
