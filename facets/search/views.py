from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.template import loader
import json

from elasticsearch import Elasticsearch

from lib.process import ScoreProcessing
from lib.search.IndexWrapper import IndexWrapper
from lib.search.SearchContext import *
from django.conf import settings
import requests

import urllib.parse

from rest.models import *

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
    # Find composer names in all indexes
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

def fetch_query(request):
    # Fetch query in abc format

    """
    #the commented code does not work, has to save it as file then open
    tempcontext = SearchContext()
    tempcontext.pattern = pattern
    abcpattern = tempcontext.check_default_meter()
    if pattern == None:
        return HttpResponse("No query for display.")
    return HttpResponse(abcpattern)
    """

    return


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
                    matching_info_dict = {}
                    # Get a list of doc_id and composer names
                    for hit in matching_docs.hits.hits:
                        if 'composer' in hit['_source']:
                            matching_composers.append(hit['_source']['composer'])
                            matching_info_dict[hit['_id']] = hit['_source']['composer']
                        matching_doc_ids.append(hit['_id'])

                    # Get rid of duplicates
                    invalid_name = [""]
                    matching_composers = list(set(matching_composers)-set(invalid_name))

                    # TODO: Faceted filter(only composer for the moment)
                    filtered_doc_ids = []
                    # only one name at this moment but should be a list
                    if searchinput["composer"]:
                        for i in matching_doc_ids:
                           if matching_info_dict[i] == searchinput["composer"]: # later change to "in" when searchinput["composer"] becomes a list
                                filtered_doc_ids.append(i)
                        # only match the filtered ones, discard others
                        matching_doc_ids = filtered_doc_ids
                
                    # Get matching ids(positions) of patterns in MusicSummary for highlighting
                    matching_locations = index_wrapper.locate_matching_patterns(searchinput["index_name"], matching_doc_ids, searchcontext)

                    # Display the list: number of pattern occurrences in every matching doc
                    # This should not be useful in final result view
                    match_dict_display = {}
                    num_matching_patterns = 0
                    for mat_doc in matching_locations:
                        num_matching_patterns += mat_doc["num_occu"]
                        print("There are", mat_doc["num_occu"]," matching patterns in doc id:", mat_doc["doc"])
                        print("ids of all matching notes are:", mat_doc["matching_ids"], "\n")
                        match_dict_display[mat_doc["doc"]] = mat_doc["num_occu"]

                    hostname = request.get_host()
                    score_info = {}
                    # Score info(type, media link) for score display:
                    for doc_id in matching_doc_ids:
                        try:
                            musicdoc = MusicDoc.objects.get(doc_id=doc_id)
                            score_info[doc_id] = []
                            score_info[doc_id].append(musicdoc.doc_type)
                            docurl = "http://"+hostname+ "/home/media/"+searchinput["index_name"]+"/"+doc_id+"/"
                            score_info[doc_id].append(docurl)
                            if musicdoc.title:
                                score_info[doc_id].append(musicdoc.title)
                            else:
                                score_info[doc_id].append("Unknown title")
                            if musicdoc.composer:
                                score_info[doc_id].append(musicdoc.composer)
                            else:
                                score_info[doc_id].append("Unknown composer")
                        except Exception as ex:
                            return HttpResponse(str(ex))

                    # the idea is to get url for abc pattern display,
                    # but the only way to do it is to save the query
                    abcurl = "http://"+hostname+"/search/query/"#+searchinput["pattern"]+"/"

                else:
                    # TODO: lyrics?
                    match_dict_display = {}
                    score_info = {}
                    num_matching_patterns = 0

                #except Exception as ex:
                #    print("Error occurred while searching on ES index:", str(ex))

                #print("Matching documents are:", matching_doc_ids)

                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "results": match_dict_display,
                    "indices_names": indices,
                    "searchcontext": searchcontext,
                    "num_matching_docs": len(matching_doc_ids),
                    "num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    "matching_composers": matching_composers,
                    "matching_locations": matching_locations,
                    "score_info": score_info,
                    "query_url": abcurl
                }

                return HttpResponse(template.render(context, request))
        elif request.method == 'GET':
            # should not be called at this moment
            return HttpResponse("Please return and search again.")

    def HighlightMusicDocView(request, doc_id):
        # Highlight patterns while viewing a music document
        # not in use right now!!

        """
        TODO:
        1. HOW to modify the code in results-list.html to redirect it with the attribute of index name?
        2. HOW to get the ids to highlight from def result?

        3. HOW to highlight with verovio toolkit?
    
        #if request.method == 'GET':
        #    highlight_ids = request.GET.get('matching_doc_ids')
        #try:
            # highlight_ids = matching_locations[doc_id]["matching_ids"]
        #except Exception as ex:
        #    print("Error occurred while getting ids to highlight:", str(ex))

        """
        template = loader.get_template('search/highlight_musicdoc.html')

        try:
            musicdoc = MusicDoc.objects.get(doc_id=doc_id)
        except Exception as ex:
            return HttpResponse("No music document found in database.")

        hostname = request.get_host()
        doc_url = "http://"+hostname+ "/home/media/"+index_name+"/"+doc_id+"/"

        context = {
            "index_name": index_name,
            "doc_type": musicdoc.doc_type,
            "doc_id": doc_id,
            "doc_url": doc_url#,
            #"highlight_ids": highlight_ids
        }
        return HttpResponse(template.render(context, request))


