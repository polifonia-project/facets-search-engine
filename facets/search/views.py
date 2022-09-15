from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
import json

from elasticsearch import Elasticsearch

from lib.process import ScoreProcessing
from lib.search.IndexWrapper import IndexWrapper
from lib.search.SearchContext import *
from django.conf import settings
import requests

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[
        {'host': host, 'port': settings.ELASTIC_SEARCH["port"]},
        {'host': "FACETS-ES", 'port': 9200},
        {'host': "0.0.0.0", 'port': 9200},
        {'host': "127.0.0.1", 'port': 9200}
    ])
except:
    print("\n\n******Error connecting to Elasticsearch, please check your if it is running.")

def index(request):
    indices = es.indices.get_alias().keys()

    """
    # Composer names in all indexes
    composer_names = []
    if indices != {}:
        # Any index will do
        anyindex = next(iter(indices))
        index_wrapper = IndexWrapper(anyindex)
        composer_names = index_wrapper.get_composer_names()
    """
    
    context = {"indices_names": indices}#, "composer_names": composer_names}

    template = loader.get_template('search/index.html')
    return HttpResponse(template.render(context, request))

class search_results:

    def __init__(self):
        return

    def results(request):
        # print("result view called")

        es = Elasticsearch()
        indices = es.indices.get_alias().keys()

        if request.method == 'POST':
            #try:
                searchinput = {}
                searchinput["pattern"] = request.POST.get('pattern', False)
                if request.POST.get('mirror', False):
                    searchinput["mirror"] = True
                else:
                    searchinput["mirror"] = False

                searchinput["pianopattern"] = request.POST.get('pianopattern', False)

                searchinput["type"] = request.POST.get('searchtype', False)
                # The search type names for ES should be all in lower case
                searchinput["type"] = searchinput["type"].lower()

                searchinput["index_name"] = request.POST.get('indexname', False)
                # TO-DO: Forcing index_name to be all lower case might cause error.
                # Find a better fix: do not put the first letter as captial letter when displaying/send through request
                searchinput["index_name"] = searchinput["index_name"].lower()

                searchinput["composer"] = request.POST.get('composer', False)

                print("piano pattern:", searchinput["pianopattern"])
            
                #req = Request('GET',  url, data=data, headers=headers)
                # if the user views a musicdoc
                #HttpResponseRedirect(reverse('highlight_musicdoc'), context)


                if searchinput["pattern"] or searchinput["pianopattern"]:

                    #print(searchinput)
                    searchcontext = SearchContext()
                    # json -> searchcontext
                    searchcontext.read(searchinput)
                    # print the content of SearchContext object
                    print("\n\nSearching in index: ", searchcontext.index)
                    print("Search type: ", searchcontext.search_type)
                    if searchcontext.pattern:
                        print("ABC encoded pattern: ", searchcontext.pattern)
                    elif searchcontext.pianopattern:
                        print("Pattern from piano", searchcontext.pianopattern)

                    if not searchcontext.check_pattern_length():
                        # TODO: test this and show render in htmlresponse if pattern is too short
                        searchcontext.pattern = ""
                        searchcontext.pianopattern = ""
                        if searchcontext.keywords != "":
                            print("Pattern not valid, we are in keyword search mode.")
                        else:
                            print ("Please re-enter a valid pattern: it must contain at least three intervals")

                    if searchcontext.text:
                        print("Text: ", searchcontext.text)
                    if searchcontext.facet_composers != [] and searchinput["composer"] != False:
                        # MAKE SURE ALL THE NAMES ARE THE ORIGINAL INPUT IN CASE OF UPPER AND LOWER CASE
                        print("Faceted: search for work composed by:")
                        for composer in searchcontext.facet_composers:
                            print(composer)
                    if searchcontext.search_type != "lyrics":
                        print("Mirror search: ", searchcontext.mirror_search,"\n\n")

                    index_wrapper = IndexWrapper(searchinput["index_name"])
                    # ES returns a "response" object with all the documents that matches query
                    matching_docs = index_wrapper.search(searchcontext)

                    matching_doc_ids = []
                    matching_composers = []

                    # Get a list of doc_id and composer names
                    for hit in matching_docs.hits.hits:
                        if 'composer' in hit['_source']:
                            matching_composers.append(hit['_source']['composer'])
                        matching_doc_ids.append(hit['_id'])

                    # Get rid of duplicates
                    invalid_name = [""]
                    matching_composers = list(set(matching_composers)-set(invalid_name))


                    """
                    # if there is a list of selected composers, filter the matching docs:
                    if searchinput["composer"] != [] and searchinput["composer"] != False:
                        for hit in matching_docs.hits.hits:
                            if 'composer' in hit['_source']:
                                if hit['_source']['composer'] in searchinput["composer"]:
                                    matching_doc_ids.append(hit['_id'])
                                    matching_composers.append()
                    """
                
                    # Get matching ids(positions) of patterns in MusicSummary for highlighting
                    matching_locations = index_wrapper.locate_matching_patterns(searchinput["index_name"], matching_doc_ids, searchcontext)

                    match_dict_display = {}
                    num_matching_patterns = 0
                    for mat_doc in matching_locations:
                        num_matching_patterns += mat_doc["num_occu"]
                        print("There are", mat_doc["num_occu"]," matching patterns in doc id:", mat_doc["doc"])
                        print("ids of all matching notes are:", mat_doc["matching_ids"], "\n")
                        match_dict_display[mat_doc["doc"]] = mat_doc["num_occu"]

                else:
                    # TODO: lyrics?
                    match_dict_display = {}
                    num_matching_patterns = 0

            #except Exception as ex:
            #    print("Error occurred while searching on ES index:", str(ex))

        template = loader.get_template('search/results.html')
        context = {
            "searchinput": searchinput,
            "results": match_dict_display,
            "indices_names": indices,
            "searchcontext": searchcontext,
            "num_matching_docs": len(matching_doc_ids),
            "num_matching_patterns": num_matching_patterns,
            "matching_doc_ids": matching_doc_ids,
            "matching_composers": matching_composers,
            "matching_locations": matching_locations
        }

        return HttpResponse(template.render(context, request))

    def HighlightMusicDocView(request, doc_id):
        # Highlight patterns while viewing a music document

        #try:
            # highlight_ids = matching_locations[doc_id]["matching_ids"]
        #except Exception as ex:
        #    print("Error occurred while getting ids to highlight:", str(ex))
        template = loader.get_template('search/highlight_musicdoc.html')

        if request.method == 'GET':
            highlight_ids = request.GET.get('matching_doc_ids')


        # TODO: this highlight_musicdoc.html needs to be written
        context = {
            "doc_id": doc_id,
            "highlight_ids": highlight_ids
        }

        return HttpResponse(template.render(context, request))


