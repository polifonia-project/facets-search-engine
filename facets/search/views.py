from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
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
    # host = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"]
    hp = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"][0]
    host=hp["host"]
    port=hp["port"]
    es = Elasticsearch(hosts=[ {'host': host, 'port': port}, ])
except:
    print("\n\n**home**** Error connecting to Elasticsearch, please check your if it is running.")


def index(request):
    try:
        indices = es.indices.get_alias().keys()
    except:
        template = loader.get_template('home/es_errorpage.html')
        context = {}
        return HttpResponse(template.render(context, request))

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

class search_results:

    def __init__(self):
        return

    def results(request):
        # print("result view called")

        es = Elasticsearch()
        try:
            indices = es.indices.get_alias().keys()
        except:
            # if ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if request.method == 'POST':
            try:
                searchinput = {}
                searchinput["pattern"] = request.POST.get('pattern', False)
                if request.POST.get('mirror', False):
                    searchinput["mirror"] = True
                else:
                    searchinput["mirror"] = False

                searchinput["pianopattern"] = request.POST.get('pianopattern', False)
                searchinput["rankby"] = request.POST.get('rankby', False)

                searchinput["type"] = request.POST.get('searchtype', False)
                # The search type names for ES should be all in lower case
                searchinput["type"] = searchinput["type"].lower()

                searchinput["index_name"] = request.POST.get('indexname', False)
                # TO-DO: Forcing index_name to be all lower case might cause error.
                # Find a better fix: do not put the first letter as captial letter when displaying/send through request
                searchinput["index_name"] = searchinput["index_name"].lower()

                searchinput["composer"] = request.POST.get('composer', False)

                if searchinput["pattern"] or searchinput["pianopattern"]:
                    searchcontext = SearchContext()
                    # json -> searchcontext
                    searchcontext.read(searchinput)
                    # print the content of SearchContext object
                    print("\n\nSearching in index: ", searchcontext.index)
                    print("Search type: ", searchcontext.search_type)
                    if searchcontext.pattern:
                        print("ABC encoded pattern: ", searchcontext.pattern)
                    elif searchcontext.pianopattern:
                        print("Pattern from piano: ", searchcontext.pianopattern)

                    if not searchcontext.check_pattern_length():
                        # TODO: test this and show render in htmlresponse if pattern is too short
                        searchcontext.pattern = ""
                        searchcontext.pianopattern = ""
                        if searchcontext.keywords != "":
                            print("Pattern not valid, we are in keyword search mode.")
                        else:
                            print("Please re-enter a valid pattern: it must contain at least three intervals")
                            template = loader.get_template('search/search_errorpage.html')
                            context = {"indices_names": indices}
                            return HttpResponse(template.render(context, request))
                            
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

                    # Get matching ids(positions) of patterns in MusicSummary for highlighting
                    matching_locations = index_wrapper.locate_matching_patterns(searchinput["index_name"], matching_doc_ids, searchcontext)

                    # Display the list: number of pattern occurrences in every matching doc
                    # For rank by relevancy
                    match_dict_display = {}
                    num_matching_patterns = 0
                    for mat_doc in matching_locations:
                        num_matching_patterns += mat_doc["num_occu"]
                        print("There are", mat_doc["num_occu"]," matching patterns in doc id:", mat_doc["doc"])
                        print("ids of all matching notes are:", mat_doc["matching_ids"], "\n")
                        match_dict_display[mat_doc["doc"]] = mat_doc["num_occu"]

                    if searchinput["rankby"] == "relevancy":
                        matching_doc_ids = sorted(match_dict_display, key=match_dict_display.get)
                        
                    # Get rid of duplicates
                    invalid_name = [""]
                    matching_composers = list(set(matching_composers)-set(invalid_name))

                    filtered_doc_ids = []
                    # TODO not urgent: only one name at this moment but should be a list
                    if searchinput["composer"]:
                        for i in matching_doc_ids:
                           if matching_info_dict[i] == searchinput["composer"]: # later change to "in" when searchinput["composer"] becomes a list
                                filtered_doc_ids.append(i)
                        # only match the filtered ones, discard others
                        matching_doc_ids = filtered_doc_ids

                    hostname = request.get_host()
                    score_info = {}
                    # Score info(type, media link) for score display:
                    for doc_id in matching_doc_ids:
                        try:
                            musicdoc = MusicDoc.objects.get(doc_id=doc_id)
                        except Exception as ex:
                            # If exception raised here, there's something indexed on ES but not in database. 
                            template = loader.get_template('error.html')
                            error_message = str(ex)+'\n'
                            error_message += "Please re-upload document:"+doc_id+" to make sure all documents indexed ES are stored in database."
                            context = {"message": error_message}
                            return HttpResponse(template.render(context, request))

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

                else:
                    # TODO: lyrics and text, right now just leave them empty
                    match_dict_display = {}
                    score_info = {}
                    num_matching_patterns = 0

                request.session["matching_locations"] = matching_locations
                request.session["searchinput"] = searchinput
                request.session["num_matching_patterns"] = num_matching_patterns
                request.session["matching_doc_ids"] = matching_doc_ids
                request.session["matching_composers"] = matching_composers
                request.session["matching_locations"] = matching_locations
                #request.session["score_info"] = score_info
                request.session["match_dict_display"] = match_dict_display

                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "searchcontext": searchcontext,
                    "num_matching_docs": len(matching_doc_ids),
                    "num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    "matching_composers": matching_composers,
                    "matching_locations": matching_locations,
                    "score_info": score_info,
                    "abcpattern": searchinput["pattern"]
                }

                return HttpResponse(template.render(context, request))
            except Exception as ex: 
                print((str(ex)))
                template = loader.get_template('search/search_errorpage.html')
                context = {"indices_names": indices}
                return HttpResponse(template.render(context, request))

        elif request.method == 'GET':
            template = loader.get_template('search/search_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

    def HighlightMusicDocView(request, index_name, doc_id):
        # Highlight patterns while viewing a music document
    
        template = loader.get_template('search/highlight_musicdoc.html')

        all_matching = request.session.get('matching_locations')
        # Find the list of ids to highlight in this doc
        for dict_i in all_matching:
            if dict_i["doc"] == doc_id:
                highlight_ids = dict_i["matching_ids"]

        # Get url to display the doc
        try:
            musicdoc = MusicDoc.objects.get(doc_id=doc_id)
        except Exception as ex:
            return HttpResponse("No music document found in database.")

        hostname = request.get_host()
        doc_url = "http://"+hostname+ "/home/media/"+index_name+"/"+doc_id+"/"

        context = {
            "index_name": index_name,
            "doc_type": musicdoc.doc_type,
            "composer": musicdoc.composer,
            "title": musicdoc.title,
            "doc_id": doc_id,
            "doc_url": doc_url,
            "highlight_ids": highlight_ids
        }
        return HttpResponse(template.render(context, request))

    def FilteredResultView(request):
        # Ideally, this page does not display the search input anymore 
        # because the user should not submit a new search input from this page
        # kept for now for information, should be removed once there's score display for search input

        es = Elasticsearch()
        try:
            indices = es.indices.get_alias().keys()
        except:
            # If ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if request.method == 'POST':

            template = loader.get_template('search/filtered_result.html')

            searchinput = request.session.get('searchinput')

            # for stats display
            num_matching_patterns = request.session.get("num_matching_patterns")
            matching_doc_ids = request.session.get("matching_doc_ids")
            num_matching_docs = len(matching_doc_ids)

            # for display in the composer facets
            matching_composers = request.session.get("matching_composers")
            # for highlighting
            matching_locations = request.session.get("matching_locations")
            # for ranking by relevancy
            match_dict_display = request.session.get("match_dict_display")

            # TODO: only one name at this moment but should be a list
            searchinput["composer"] = request.POST.get('composer', False)

            searchinput["rankby"] = request.POST.get('rankby', False)
            print(searchinput["rankby"])
            if searchinput["rankby"] == "relevancy" or searchinput["rankby"] == "Relevancy":
                print("Before re-rank, matching docs are:", matching_doc_ids)
                matching_doc_ids = sorted(match_dict_display, key=match_dict_display.get)
                matching_doc_ids = list(reversed(matching_doc_ids))
                print("After re-rank, matching docs are:", matching_doc_ids)

            hostname = request.get_host()
            score_info = {}
            # Score info(type & media link) for preview of matching scores in result page:
            for doc_id in matching_doc_ids:
                try:
                    musicdoc = MusicDoc.objects.get(doc_id=doc_id)
                except Exception as ex:
                    # There's something indexed on ES but not in database.
                    # Solution of this error is: re-upload unsync document(s)
                    template = loader.get_template('error.html')
                    error_message = str(ex)+'\n'
                    error_message += "Please re-upload document:"+doc_id+" to make sure all documents indexed ES are stored in database."
                    context = {"message": error_message}
                    return HttpResponse(template.render(context, request))

                if searchinput["composer"] != False:
                    # filter out the ones that is not selected composer, if there is a composer facet selected
                    if musicdoc.composer != searchinput["composer"]:
                        continue

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

            context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "num_matching_docs": num_matching_docs,
                    "num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    "matching_composers": matching_composers,
                    "matching_locations": matching_locations,
                    "score_info": score_info
            }

            return HttpResponse(template.render(context, request))
