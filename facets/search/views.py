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
host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
es = Elasticsearch(hosts=[{'host': host, 'port': 9200}],)

def index(request):
    indices = es.indices.get_alias().keys()
    context = {"indices_names": indices}

    template = loader.get_template('search/index.html')
    return HttpResponse(template.render(context, request))

@csrf_exempt
def results(request):
    # print("result view called")

    es = Elasticsearch()
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
            searchinput["type"] = searchinput["type"].lower()

            searchinput["index_name"] = request.POST.get('indexname', False)
            # Maybe there is a better fix than forcing the input to be lower case?
            searchinput["index_name"] = searchinput["index_name"].lower()

            if searchinput["pattern"]:
                print(searchinput)
                searchcontext = SearchContext()
                # json -> searchcontext
                searchcontext.read(searchinput)
                # print the content of SearchContext object
                print("\n\nSearching in index: ", searchinput["index_name"])
                print("search type: ", searchcontext.search_type)
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
                matching_doc_ids = []
                for hit in matching_docs.hits.hits:
                    matching_doc_ids.append(hit['_id'])
                print("Matching documents are:", matching_doc_ids)

                # Get matching ids(positions) of patterns in MusicSummary for highlighting
                matching_locations = index_wrapper.locate_matching_patterns(searchinput["index_name"], matching_doc_ids, searchcontext)

                match_dict_display = {}
                for mat_doc in matching_locations:
                    print("There are", mat_doc["num_occu"]," matching patterns in doc id:", mat_doc["doc"])
                    print("ids of all matching notes are:", mat_doc["matching_ids"], "\n")
                    match_dict_display[mat_doc["doc"]] = mat_doc["num_occu"]

        except Exception as ex:
            print("Error occurred while searching on ES index:", str(ex))

    template = loader.get_template('search/results.html')
    context = {
        "searchinput": searchinput,
        "results": match_dict_display,
        "indices_names": indices}
    return HttpResponse(template.render(context, request))
