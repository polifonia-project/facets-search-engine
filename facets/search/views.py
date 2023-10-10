from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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

hp = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"][0]
elastic_params = "http://"+hp["host"]+":"+str(hp["port"])


def index(request):
    try:
        es = Elasticsearch(elastic_params)
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
    
    context = {"indices_names": indices, 
               "disable_scorelib": settings.DISABLE_SCORELIB
              }#, "composer_names": composer_names}

    template = loader.get_template('search/index.html')
    return HttpResponse(template.render(context, request))

class search_results:

    def __init__(self):
        return

    def read_search_input_from_request(request, searchinput):
        
        if searchinput == {}:
            # if it is the first entry of search with pattern, read them
            searchinput["pattern"] = request.POST.get('pattern', False)
            if request.POST.get('mirror', False):
                searchinput["mirror"] = True
            else:
                searchinput["mirror"] = False

            searchinput["pianopattern"] = request.POST.get('pianopattern', False)
            searchinput["type"] = request.POST.get('searchtype', False)
            # The search type names for ES should be all in lower case
            searchinput["type"] = searchinput["type"].lower()

        # Ranking
        searchinput["rankby"] = request.POST.get('rankby', False)

        # Index
        if "index_name" not in searchinput:
            searchinput["index_name"] = request.POST.get('indexname', False)
            # Find a better fix: do not put the first letter as captial letter when displaying/send through request

            invalid_names = ["", "Not selected", "not selected"]
            if searchinput["index_name"]:
                if searchinput["index_name"] not in invalid_names:
                    searchinput["index_name"] = searchinput["index_name"].lower()
        # otherwise ignore the input

        # Facets

        searchinput["composer"] = request.POST.get('composer', False)
        searchinput["instrument"] = request.POST.get('instrument', False)
        searchinput["period"] = request.POST.get('period', False)
        #searchinput["keymode"] = request.POST.get('keymode', False)
        #searchinput["keytonicname"] = request.POST.get('keytonicname', False)
        searchinput["key"] = request.POST.get('key', False)
        searchinput["numofparts"] = request.POST.get('numofparts', False)
        searchinput["numofmeasures"] = request.POST.get('numofmeasures', False)
        #searchinput["numofnotes"] = request.POST.get('numofnotes', False)
        searchinput["timesig"] = request.POST.get('timesig', False)
  
        # facets to be continued

        return searchinput

    def read_pattern_search_into_search_context(searchinput):
        
        searchcontext = SearchContext()
        # json -> searchcontext
        searchcontext.read(searchinput)
        
        # print the content of SearchContext object, for testing
        if searchcontext.index != "ALL_INDICES":
            print("\n\nSearching in index: ", searchcontext.index)
        else:
            print("\n\nSearching in all indices ")

        print("Search type: ", searchcontext.search_type)
        
        if searchcontext.pattern:
            print("ABC encoded pattern: ", searchcontext.pattern)
        elif searchcontext.pianopattern:
            print("Pattern from piano: ", searchcontext.pianopattern)
        
        # Print some info about the search
        if searchcontext.text:
            print("Text: ", searchcontext.text)
        # Print info about faceting
        if searchcontext.facet_composers != [] and searchinput["composer"] != False and searchcontext.facet_composers != "":
            # MAKE SURE ALL THE NAMES ARE THE ORIGINAL INPUT IN CASE OF UPPER AND LOWER CASE
            print("Faceted: search for work composed by:", searchcontext.facet_composers)
        if searchcontext.facet_instruments != [] and searchinput["instrument"] != False and searchcontext.facet_instruments != "":
            print("Faceted: search for work with the following instruments:", searchcontext.facet_instruments)
        if searchcontext.facet_key != "" and searchinput["key"] != False:
            print("Faceted: search for work of the following key information:", searchcontext.facet_key)
        if searchcontext.facet_period != "" and searchinput["period"] != False:
            print("Faceted: search for work of the following period:", searchcontext.facet_period)

        """
        # these two are combined into one
        if searchcontext.facet_keymode != "" and searchinput["keymode"] != False:
            print("Faceted: search for work with the following key mode:", searchcontext.facet_keymode)
        if searchcontext.facet_keytonicname != "" and searchinput["keytonicname"] != False:
            print("Faceted: search for work with the following key tonic name:", searchcontext.facet_keytonicname)
        """
        if searchcontext.facet_numofparts != "" and searchinput["numofparts"] != False:
            print("Faceted: search for work of the following num of parts:", searchcontext.facet_numofparts)
        if searchcontext.facet_numofmeasures != "" and searchinput["numofmeasures"] != False:
            print("Faceted: search for work of the following num of measures:", searchcontext.facet_numofmeasures)
        #if searchcontext.facet_numofnotes != "" and searchinput["numofnotes"] != False:
        #    print("Faceted: search for work of the following num of notes:", searchcontext.facet_numofnotes)
        if searchcontext.facet_timesig != "" and searchinput["timesig"] != False:
            print("Faceted: search for work of the following time signature:", searchcontext.facet_timesig)

        #TBC.. for other facets

        if searchcontext.search_type != "lyrics":
            print("Mirror search: ", searchcontext.mirror_search, "\n\n")

        return searchcontext

    def get_info_from_matching_docs(matching_docs):
        # Get matching_doc_ids and metadata info from each matching docs.

        # Currently, matching info is not useful.
        # but if meta info needs to be displayed in the page of search results, it becomes useful..

        matching_info = {}
        matching_doc_ids = []

        for hit in matching_docs.hits.hits:
            matching_info[hit['_id']] = {}
            
            # Get composer info
            if 'composer' in hit['_source']:
                matching_info[hit['_id']]['composer'] = hit['_source']['composer']
            matching_doc_ids.append(hit['_id'])

            # Get instrument info
            if 'infos' in hit['_source']:
                if 'instruments' in hit['_source']['infos']:
                    if hit['_source']['infos']['instruments'] != [] and hit['_source']['infos']['instruments'] != None:
                        matching_info[hit['_id']]['instruments'] = hit['_source']['infos']['instruments']
                """
                if 'key_mode' in hit['_source']['infos']:
                    if hit['_source']['infos']['key_mode'] != [] and hit['_source']['infos']['key_mode'] != None:
                        matching_info[hit['_id']]['key_mode'] = hit['_source']['infos']['key_mode']

                if 'key_tonic_name' in hit['_source']['infos']:
                    if hit['_source']['infos']['key_tonic_name'] != [] and hit['_source']['infos']['key_tonic_name'] != None:
                        matching_info[hit['_id']]['key_tonic_name'] = hit['_source']['infos']['key_tonic_name']
                """
                if 'key' in hit['_source']['infos']:
                    if hit['_source']['infos']['key'] != [] and hit['_source']['infos']['key'] != None:
                        matching_info[hit['_id']]['key'] = hit['_source']['infos']['key']

                if 'period' in hit['_source']['infos']:
                    if hit['_source']['infos']['period'] != [] and hit['_source']['infos']['period'] != None:
                        matching_info[hit['_id']]['period'] = hit['_source']['infos']['period']

                if 'num_of_parts' in hit['_source']['infos']:
                    if hit['_source']['infos']['num_of_parts'] != [] and hit['_source']['infos']['num_of_parts'] != None:
                        matching_info[hit['_id']]['num_of_parts'] = hit['_source']['infos']['num_of_parts']

                if 'num_of_measures' in hit['_source']['infos']:
                    if hit['_source']['infos']['num_of_measures'] != [] and hit['_source']['infos']['num_of_measures'] != None:
                        matching_info[hit['_id']]['num_of_measures'] = hit['_source']['infos']['num_of_measures']
                """
                if 'num_of_notes' in hit['_source']['infos']:
                    if hit['_source']['infos']['num_of_notes'] != [] and hit['_source']['infos']['num_of_notes'] != None:
                        matching_info[hit['_id']]['num_of_notes'] = hit['_source']['infos']['num_of_notes']
                """
                if 'initial_time_signature' in hit['_source']['infos']:
                    if hit['_source']['infos']['initial_time_signature'] != [] and hit['_source']['infos']['initial_time_signature'] != None:
                        matching_info[hit['_id']]['timesig'] = hit['_source']['infos']['initial_time_signature']

            # Get more info... to be continued

        return matching_doc_ids, matching_info

    def count_facets_from_agg(matching_docs):

                    # dictionary of dictionary of each facet
                    facets_count_dict = {}

                    # for filtering out invalid names
                    invalid_name = ["", "composers", "Composers", "instruments", "Instruments", "Period", "period", "Key mode", "Key Mode", "Key tonic name", "key tonic name", "Num of parts", "num of parts", "Num of measures", "num of measures", "num of notes", "Num of notes", "Time signature", "Time Signature", "Key", "key", "Not selected", "not selected"]

                    # Get a dictionary of all composer names in the matching docs and the number of docs for each compoer
                    facet_composers = {}
                    facet_hit_ids = {}
                    facet_hit_ids['composer'] = {}
                    for composer in matching_docs.aggregations.per_composer.buckets:
                        #print(composer) # just for testing
                        # composer.key is composer name, composer.doc_count is num of docs composed by this composer
                        facet_composers[composer.key] = composer.doc_count
                        list_ids_curr_composer = []
                        # get each hit doc id for curr composer
                        for item in composer.top_hits.buckets:
                            list_ids_curr_composer.append(item['key'])
                        facet_hit_ids['composer'][composer.key] = list_ids_curr_composer
                    facet_composers = list(set(facet_composers)-set(invalid_name))
                    facets_count_dict["composer"] = facet_composers

                    facet_instruments = {}
                    facet_hit_ids['instrument'] = {}                    
                    # Get a dictionary of all instrument names in the matching docs and the number of matches for each instrument
                    for instrument in matching_docs.aggregations.per_instrument.buckets:
                        #print(instrument) # just for testing
                        facet_instruments[instrument.key] = instrument.doc_count
                        list_ids_curr_instr = []
                        # get each hit doc id for curr composer
                        for item in instrument.top_hits.buckets:
                            list_ids_curr_instr.append(item['key'])
                        facet_hit_ids['instrument'][instrument.key] = list_ids_curr_instr
                    facet_instruments = list(set(facet_instruments)-set(invalid_name))
                    facets_count_dict["instrument"] = facet_instruments


                    facet_period = {}
                    facet_hit_ids['period'] = {}                    
                    # Get a dictionary of all period names in the matching docs and the number of matches for each period
                    for period in matching_docs.aggregations.per_period.buckets:
                        facet_period[period.key] = period.doc_count
                        list_ids_curr_per = []
                        # get each hit doc id for curr composer
                        for item in period.top_hits.buckets:
                            list_ids_curr_per.append(item['key'])
                        facet_hit_ids['period'][period.key] = list_ids_curr_per
                    facet_period = list(set(facet_period)-set(invalid_name))
                    facets_count_dict["period"] = facet_period

                    facet_key = {}
                    facet_hit_ids['key'] = {}
                    # Get a dictionary of all key names in the matching docs and the number of matches for each key
                    for key in matching_docs.aggregations.per_key.buckets:
                        #print(keytonicname) # just for testing
                        facet_key[key.key] = key.doc_count                        
                        list_ids_curr_key = []
                        # get each hit doc id for curr composer
                        for item in key.top_hits.buckets:
                            list_ids_curr_key.append(item['key'])
                        facet_hit_ids['key'][key.key] = list_ids_curr_key

                    facet_key = list(set(facet_key)-set(invalid_name))
                    facets_count_dict["key"] = facet_key
                    
                    facet_numofparts = {}
                    facet_hit_ids['numofparts'] = {}
                    for numofparts in matching_docs.aggregations.per_parts.buckets:
                        #print(numofparts) # just for testing
                        facet_numofparts[numofparts.key] = numofparts.doc_count                        
                        list_ids_curr_parts = []
                        # get each hit doc id 
                        for item in numofparts.top_hits.buckets:
                            list_ids_curr_parts.append(item['key'])
                        facet_hit_ids['numofparts'][numofparts.key] = list_ids_curr_parts

                    facet_numofparts = list(set(facet_numofparts)-set(invalid_name))
                    facets_count_dict["numofparts"] = facet_numofparts

                    facet_numofmeasures = {}
                    facet_hit_ids['numofmeasures'] = {}
                    for numofmeasures in matching_docs.aggregations.per_measures.buckets:
                        #print(keytonicname) # just for testing
                        facet_numofmeasures[numofmeasures.key] = numofmeasures.doc_count                        
                        list_ids_curr_mea = []
                        # get each hit doc id 
                        for item in numofmeasures.top_hits.buckets:
                            list_ids_curr_mea.append(item['key'])
                        facet_hit_ids['numofmeasures'][numofmeasures.key] = list_ids_curr_mea

                    facet_numofmeasures = list(set(facet_numofmeasures)-set(invalid_name))
                    facets_count_dict["numofmeasures"] = facet_numofmeasures
                    """
                    facet_numofnotes = {}
                    facet_hit_ids['numofnotes'] = {}
                    for numofnotes in matching_docs.aggregations.per_notes.buckets:
                        #print(numofnotes) # just for testing
                        facet_numofnotes[numofnotes.key] = numofnotes.doc_count
                        list_ids_curr_notes = []
                        # get each hit doc id 
                        for item in numofnotes.top_hits.buckets:
                            list_ids_curr_notes.append(item['key'])
                        facet_hit_ids['numofnotes'][numofnotes.key] = list_ids_curr_notes

                    facet_numofnotes = list(set(facet_numofnotes)-set(invalid_name))
                    facets_count_dict["numofnotes"] = facet_numofnotes
                    """
                    facet_timesig = {}
                    facet_hit_ids['timesig']= {}
                    for timesig in matching_docs.aggregations.per_timesig.buckets:
                        #print(numofnotes) # just for testing
                        facet_timesig[timesig.key] = timesig.doc_count
                        list_ids_curr_timesig = []
                        # get each hit doc id 
                        for item in timesig.top_hits.buckets:
                            list_ids_curr_timesig.append(item['key'])
                        facet_hit_ids['timesig'][timesig.key] = list_ids_curr_timesig

                    facet_timesig = list(set(facet_timesig)-set(invalid_name))
                    facets_count_dict["timesig"] = facet_timesig

                    # TO BE CONTINUED: other facets

                    return facets_count_dict, facet_hit_ids

    def get_faceted_matching_ids(search_context, matching_doc_ids, facet_hit_ids):

            temp_matching_ids = []
            # List of doc ids that meets all faceting requirement
            common_list = matching_doc_ids

            if search_context.facet_composers != None and search_context.facet_composers != [] and search_context.facet_composers != "":
                # note: this needs to change when it's a list instead of one input for faceting
                if search_context.facet_composers in facet_hit_ids["composer"]:
                    temp_matching_ids = facet_hit_ids["composer"][search_context.facet_composers]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []

            if search_context.facet_instruments != None and search_context.facet_instruments != [] and search_context.facet_instruments != "":
                # note: this needs to change when it's a list instead of one input for faceting
                if search_context.facet_instruments in facet_hit_ids["instrument"]:
                    temp_matching_ids = facet_hit_ids["instrument"][search_context.facet_instruments]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []
            """
            if search_context.facet_keymode != None and search_context.facet_keymode != "":
                if search_context.facet_keymode in facet_hit_ids["keymode"]:
                    temp_matching_ids = facet_hit_ids["keymode"][search_context.facet_keymode]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []

            if search_context.facet_keytonicname != None and search_context.facet_keytonicname != "":
                if search_context.facet_keytonicname in facet_hit_ids["keytonicname"]:
                    temp_matching_ids = facet_hit_ids["keytonicname"][search_context.facet_keytonicname]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []
            """

            if search_context.facet_period != None and search_context.facet_period != "":
                if search_context.facet_period in facet_hit_ids["period"]:
                    temp_matching_ids = facet_hit_ids["period"][search_context.facet_period]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []

            if search_context.facet_key != None and search_context.facet_key != "":
                if search_context.facet_key in facet_hit_ids["key"]:
                    temp_matching_ids = facet_hit_ids["key"][search_context.facet_key]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []

            if search_context.facet_numofparts != None and search_context.facet_numofparts != "":
                if search_context.facet_numofparts in facet_hit_ids["numofparts"]:
                    temp_matching_ids = facet_hit_ids["numofparts"][search_context.facet_numofparts]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []

            if search_context.facet_numofmeasures != None and search_context.facet_numofmeasures != "":
                if search_context.facet_numofmeasures in facet_hit_ids["numofmeasures"]:
                    temp_matching_ids = facet_hit_ids["numofmeasures"][search_context.facet_numofmeasures]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []
            """
            if search_context.facet_numofnotes != None and search_context.facet_numofnotes != "":
                if search_context.facet_numofnotes in facet_hit_ids["numofnotes"]:
                    temp_matching_ids = facet_hit_ids["numofnotes"][search_context.facet_numofnotes]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []
            """
            if search_context.facet_timesig != None and search_context.facet_timesig != "":
                if search_context.facet_timesig in facet_hit_ids["timesig"]:
                    temp_matching_ids = facet_hit_ids["timesig"][search_context.facet_timesig]
                    if (set(temp_matching_ids) & set(common_list)):
                        common_list = list(set(temp_matching_ids) & set(common_list))
                    else:
                        common_list = []

            # TBC for more facets.. 

            return common_list

    def results(request):

        es = Elasticsearch(elastic_params)
        try:
            indices = es.indices.get_alias().keys()
        except:
            # if ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if request.method == 'GET':
            # Access another page of search result
            template = loader.get_template('search/results.html')
            callpage = request.GET.get('page', False)
            context = search_results.paginate_search_result(request, callpage)
            return HttpResponse(template.render(context, request))

        if request.method == 'POST':
            try:
                callpage = request.POST.get('page', False)

                searchinput = {}
                searchinput = search_results.read_search_input_from_request(request, searchinput)

            except Exception as ex:
                template = loader.get_template('search/search_errorpage.html')
                context = {"indices_names": indices, "ex": str(ex), "message": "Error related to getting POST request!"}
                return HttpResponse(template.render(context, request))

            try:
                if searchinput["pattern"] or searchinput["pianopattern"]:
                    try:
                        searchcontext = search_results.read_pattern_search_into_search_context(searchinput)
                        if not searchcontext.check_pattern_length():
                            # if the pattern is not valid, return error
                            searchcontext.pattern = ""
                            searchcontext.pianopattern = ""
                            if searchcontext.text != "":
                                print("Pattern is not valid, we are in text search mode.")
                            else:
                                template = loader.get_template('search/search_errorpage.html')
                                error_message = "Please enter a valid pattern to search: it must contain at least three intervals"
                                context = {"indices_names": indices, "message": error_message}
                                return HttpResponse(template.render(context, request))
                    except Exception as ex:
                        template = loader.get_template('search/search_errorpage.html')
                        error_message = "Error when conversing search input into search context!"
                        context = {"indices_names": indices, "ex": str(ex), "message": error_message}
                        return HttpResponse(template.render(context, request))

                    try:
                        index_wrapper = IndexWrapper(searchinput["index_name"])
                        # ES returns a "response" object with all the documents that matches query
                        matching_docs = index_wrapper.search(searchcontext)
                    except Exception as ex:
                        template = loader.get_template('search/search_errorpage.html')
                        error_message = "Error when trying to call search with ES in IndexWrapper"
                        context = {"indices_names": indices,  "ex": str(ex), "message": error_message}
                        return HttpResponse(template.render(context, request))

                    # Get a list of doc_id and composer names
                    if matching_docs.hits.hits == []:
                        # No matching results found in this index
                        template = loader.get_template('search/results.html')
                        context = {
                            "searchinput": searchinput,
                            "index_name": searchinput["index_name"],
                            "matching_doc_ids": False,
                            "abcpattern": searchinput["pattern"],
                            "num_matching_patterns": 0 
                        }
                        return HttpResponse(template.render(context, request))

                    # Get all the matching document ids and their facets info in a dict of dicts
                    matching_doc_ids, matching_info = search_results.get_info_from_matching_docs(matching_docs)

                    # list of names of facets
                    facets_name_list = ["composer", "period", "instrument", "key", "timesig", "numofparts", "numofmeasures"]
                    # no longer needed: "keytonicname", "keymode","numofnotes",
                    # to be continued

                    # Get facets names and value
                    print("printing FACETS") # for testing only 

                    # Get a dictionary of counting for facets from aggregation for each facets
                    facets_count_dict, facet_hit_ids = search_results.count_facets_from_agg(matching_docs)
                    

                    try:
                        # Get matching ids(positions) of patterns in MusicSummary for highlighting
                        matching_locations = index_wrapper.locate_matching_patterns(searchinput["index_name"], matching_doc_ids, searchcontext)
                    except Exception as ex:
                        template = loader.get_template('search/search_errorpage.html')
                        error_message = "Error when trying to locate matching patterns in IndexWrapper"
                        context = {"indices_names": indices, "ex": str(ex), "message": error_message}
                        return HttpResponse(template.render(context, request))

                    # Display the list: number of pattern occurrences in every matching doc
                    # For rank by relevancy
                    match_dict_display = {}
                    num_matching_patterns = 0
                    for mat_doc in matching_locations:
                        num_matching_patterns += mat_doc["num_occu"]
                        print("There are", mat_doc["num_occu"]," matching patterns in doc id:", mat_doc["doc"])
                        print("ids of all matching notes are:", mat_doc["matching_ids"], "\n")
                        match_dict_display[mat_doc["doc"]] = mat_doc["num_occu"]

                    if searchinput["rankby"] == "Relevancy":
                        matching_doc_ids = sorted(match_dict_display, key=match_dict_display.get)

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
                            error_message += "Please re-upload document:"+doc_id+" to"+searchinput["index_name"]+ " to make sure all documents indexed ES are stored in database."
                            # TODO: list all the unsync docs under this index
                            context = {"message": error_message}
                            return HttpResponse(template.render(context, request))

                        score_info[doc_id] = []
                        score_info[doc_id].append(musicdoc.doc_type)
                        #docurl = "http://"+hostname+ "/home/media/"+searchinput["index_name"]+"/"+doc_id+"/"
                        docurl = "http://"+hostname+ "/home/media/"+musicdoc.index.name+"/"+doc_id+"/"

                        score_info[doc_id].append(docurl)
                        if musicdoc.title:
                            score_info[doc_id].append(musicdoc.title)
                        else:
                            score_info[doc_id].append("Unknown title")
                        if musicdoc.composer:
                            score_info[doc_id].append(musicdoc.composer.name)
                        else:
                            score_info[doc_id].append("Unknown composer")
                        score_info[doc_id].append(musicdoc.index.name)

                    # Paginator for the first page
                    if callpage == False or callpage == 0 or callpage == 1:
                        p = Paginator(tuple(score_info), settings.SCORES_PER_PAGE )
                        pg = p.get_page(1)
                        startfrom = 0
                        endby = min(settings.SCORES_PER_PAGE , p.count)
                        scores_thispg = dict(list(score_info.items())[startfrom:endby])
                    
                else:
                    # TODO: lyrics and text search, right now just give an error
                    template = loader.get_template('search/search_errorpage.html')
                    error_message = "Please enter a valid pattern to search!"
                    context = {"indices_names": indices,  "message": error_message}
                    return HttpResponse(template.render(context, request))
                    match_dict_display = {}
                    score_info = {}
                    num_matching_patterns = 0

                request.session["matching_locations"] = matching_locations
                request.session["searchinput"] = searchinput
                request.session["num_matching_patterns"] = num_matching_patterns
                request.session["matching_doc_ids"] = matching_doc_ids
                request.session["matching_locations"] = matching_locations
                request.session["score_info"] = score_info
                request.session["match_dict_display"] = match_dict_display
                # using default ranking method at the first call: rank by similarity
                request.session["ranking_method"] = "Similarity"
                #request.session["index_name"] = searchinput["index_name"]

                # save facets in request session:
                for facet_name in facets_name_list:
                    request.session[facet_name] = facets_count_dict[facet_name]
                request.session["facets_name_list"] = facets_name_list

                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "pianopattern": searchinput["pianopattern"],
                    "match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "facet_composers": facets_count_dict["composer"],
                    "facet_instruments": facets_count_dict["instrument"],
                    "facet_key": facets_count_dict["key"],
                    "facet_period": facets_count_dict["period"],
                    #"facet_keymode": facets_count_dict["keymode"],
                    #"facet_keytonicname": facets_count_dict["keytonicname"],
                    "facet_numofparts": facets_count_dict["numofparts"],
                    "facet_numofmeasures": facets_count_dict["numofmeasures"],
                    #"facet_numofnotes": facets_count_dict["numofnotes"],
                    "facet_timesig": facets_count_dict["timesig"],
                    "searchcontext": searchcontext,
                    "num_matching_docs": len(matching_doc_ids),
                    "num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    "matching_locations": matching_locations,
                    "score_info": scores_thispg,
                    "abcpattern": searchinput["pattern"],
                    "pg": pg, 
                    "startfrom": startfrom,
                    "disable_scorelib": settings.DISABLE_SCORELIB,
                    "facets_name_list": facets_name_list
                }
                return HttpResponse(template.render(context, request))
            except Exception as ex: 
                template = loader.get_template('search/search_errorpage.html')
                context = {"indices_names": indices, "ex": str(ex), "message": "other error message"}
                return HttpResponse(template.render(context, request))

    def paginate_search_result(request, callpage):
        # Pagination for the search results

        es = Elasticsearch(elastic_params)
        try:
            indices = es.indices.get_alias().keys()
        except:
            # if ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        score_info = request.session.get('score_info')
        searchinput = request.session.get('searchinput')
        match_dict_display = request.session.get("match_dict_display")
        matching_doc_ids = request.session.get("matching_doc_ids")
        num_matching_docs = len(score_info) #len(matching_doc_ids)
        num_matching_patterns = request.session.get("num_matching_patterns")
        matching_locations = request.session.get("matching_locations")
        facets_name_list = request.session.get("facets_name_list")

        # Get saved session of facets
        facets_count_dict = {}
        for facet_name in facets_name_list:
            facets_count_dict[facet_name] = request.session.get(facet_name)

        p = Paginator(tuple(score_info), settings.SCORES_PER_PAGE)

        callpage = int(callpage)
        if callpage != False:
            try:
                pg = p.get_page(callpage)
                if callpage == 0:
                    callpage = 1
                startfrom = (callpage-1)*settings.SCORES_PER_PAGE 
                endby = min(callpage*settings.SCORES_PER_PAGE , p.count)
                scores_thispg = dict(list(score_info.items())[startfrom:endby])
            except PageNotAnInteger:
                pg = p.get_page(1)
                startfrom = 0
                endby = min(settings.SCORES_PER_PAGE , p.count)
                scores_thispg = dict(list(score_info.items())[startfrom:endby])
            except EmptyPage:
                startfrom = (p.num_pages-1)*settings.SCORES_PER_PAGE 
                scores_thispg = dict(list(score_info.items())[startfrom:p.count])
                pg = p.get_page(p.num_pages)
        else:
            pg = p.get_page(1)
            startfrom = 0
            endby = min(settings.SCORES_PER_PAGE, p.count)
            scores_thispg = dict(list(score_info.items())[startfrom:endby])

        context = {
                    "searchinput": searchinput,
                    "pianopattern": searchinput["pianopattern"],
                    "index_name": searchinput["index_name"],
                    "match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "num_matching_docs": num_matching_docs,
                    "num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    "matching_locations": matching_locations,
                    "score_info": scores_thispg,
                    "abcpattern": searchinput["pattern"],
                    "pg": pg,
                    "startfrom": startfrom,
                    "disable_scorelib": settings.DISABLE_SCORELIB,
                    "facets_name_list": facets_name_list,
                    "facet_composers": facets_count_dict["composer"],
                    "facet_instruments": facets_count_dict["instrument"],
                    "facet_key": facets_count_dict["key"],
                    "facet_period": facets_count_dict["period"],
                    #"facet_keymode": facets_count_dict["keymode"],
                    #"facet_keytonicname": facets_count_dict["keytonicname"],
                    "facet_numofparts": facets_count_dict["numofparts"],
                    "facet_numofmeasures": facets_count_dict["numofmeasures"],
                    #"facet_numofnotes": facets_count_dict["numofnotes"],
                    "facet_timesig": facets_count_dict["timesig"],
        }
        return context

    def DiscoveryView(request):

        es = Elasticsearch(elastic_params)
        try:
            indices = es.indices.get_alias().keys()
            index_wrapper = IndexWrapper("ALL_INDICES")
        except:
            # if ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if  request.method == 'GET':
            template = loader.get_template('search/discovery.html')
            matching_docs = index_wrapper.get_facet_for_initial_navigation(index_name = "ALL_INDICES")

            # Now if it's empty, return empty results

            if matching_docs.hits.hits == []:
                # No matching results found in this index
                context = {
                    #"facets_count_dict": {}, 
                }
            else:
                # Get the matching doc ids with faceting
                facets_count_dict, facet_hit_ids = search_results.count_facets_from_agg(matching_docs)

                print("total hits", len(matching_docs.hits.hits))
                #print(facets_count_dict)
                print("hit id num, composer", len(facet_hit_ids["composer"]))

                facets_name_list = ["composer", "period", "instrument", "key", "timesig", "numofparts", "numofmeasures"]

                for facet_name in facets_name_list:
                    request.session[facet_name] = facets_count_dict[facet_name]
                request.session["facets_name_list"] = facets_name_list

                # get the number of matching for each facet
                # comment later, just for testing!
                #for facetname in facets_count_dict:
                #    for name in facets_count_dict[facetname]:
                #        print(facetname, name, len(facet_hit_ids[facetname][name]))

                #countnum_composer = {}
                #for composername in facet_hit_ids["composer"]:
                #    countnum_composer[composername] = len(composername)
                                
                countnum = {}
                for facet_name in facets_name_list:
                    countnum[facet_name] = {}
                    for item in facet_hit_ids[facet_name]:
                        countnum[facet_name][item] = len(facet_hit_ids[facet_name][item])
                print(countnum)

                # Get all the matching document ids and their facets info
                #matching_doc_ids, matching_info = search_results.get_info_from_matching_docs(matching_docs)

                context = {
                    "indices_names": indices,
                    #"facets_count_dict": facets_count_dict, 
                    #"facet_hit_ids": facet_hit_ids
                    "countnum": countnum,
                    "list_composer": facets_count_dict["composer"],
                    "list_period": facets_count_dict["period"],#list_period,
                    "list_key": facets_count_dict["key"],#list_key,
                    "list_timesig": facets_count_dict["timesig"],#list_timesig,
                    "list_instrument": facets_count_dict["instrument"],#list_instrument,
                    "list_numofparts": facets_count_dict["numofparts"],#list_numofparts,
                    "list_numofmeasures": facets_count_dict["numofmeasures"],#list_numofmeasures
                    #"count_composer": facet_hit_ids["composer"],
                }

            return HttpResponse(template.render(context, request))

        elif request.method == 'POST':
            DiscoveryResultView(request)

    def HighlightMusicDocView(request, index_name, doc_id):
        # Highlight patterns while viewing a music document
    
        template = loader.get_template('search/highlight_musicdoc.html')

        all_matching = request.session.get('matching_locations')
        highlight_ids = []
        # Find the list of ids to highlight in this doc
        for dict_i in all_matching:
            if dict_i["doc"] == doc_id:
                highlight_ids = dict_i["matching_ids"]

        # Get url to display the doc
        try:
            musicdoc = MusicDoc.objects.get(doc_id=doc_id)
        except Exception as ex:
            return HttpResponse(doc_id+" not found in database.")

        hostname = request.get_host()
        doc_url = "http://"+hostname+ "/home/media/"+index_name+"/"+doc_id+"/"

        context = {
            "index_name": index_name,
            "doc_type": musicdoc.doc_type,
            "composer": musicdoc.composer.name,
            "title": musicdoc.title,
            "doc_id": doc_id,
            "doc_url": doc_url,
            "highlight_ids": highlight_ids
        }
        return HttpResponse(template.render(context, request))

    def re_rank_the_results(ranking_method, match_dict_display):
        # Given a new ranking method, return the ranked list of matching doc ids for display
        if ranking_method == "Relevancy" or ranking_method == "relevancy":
            matching_doc_ids = sorted(match_dict_display, key=match_dict_display.get)
            matching_doc_ids = list(reversed(matching_doc_ids))
            return matching_doc_ids
        # TODO: rank by similarity... quick way
        #elif ranking_method == "Similarity" or ranking_method == "similarity":
            # RANK BY SIM
            # SAVE A SCORE OF THE SIMILARITY AS PART OF THE SEARCH RESULT! TODO IN IndexWrapper

    def FilteredResultView(request):
        # Ideally, this page does not display the search input anymore 
        # because the user should not submit a new search input from this page
        # kept for now for information, should be removed once there's score display for search input

        # Here score_info is changed for filtered or re-ranked display, 
        # statitstics(number of patterns and docs) are also changed.

        # TO-SOLVE(minor): if re-rank, the composer facet will be reset
        # TO-SOLVE: re-rank by similarity
        # TO-SOLVE: re-send request to ES according to the new requests
        
        es = Elasticsearch(elastic_params)
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

            # then read new entered facets and rank method
            searchinput = search_results.read_search_input_from_request(request, searchinput)

            # just a list of names of facets supported..
            facets_name_list = request.session.get("facets_name_list")

            for facet_name in facets_name_list:
                searchinput[facet_name] = request.POST.get(facet_name, False)

            if searchinput["pattern"] != "" or searchinput["pianopattern"] != "":
                # if it is pattern search
                searchcontext = search_results.read_pattern_search_into_search_context(searchinput)
                # now, send the refined search context to ES for a faceted search!
                try:
                    index_wrapper = IndexWrapper(searchinput["index_name"])
                    # ES returns a "response" object with all the documents that matches query
                    matching_docs = index_wrapper.search(searchcontext)

                    # To be continued.
                except Exception as ex:
                    template = loader.get_template('search/search_errorpage.html')
                    error_message = "Error when trying to call search with ES in IndexWrapper"
                    context = {"indices_names": indices,  "ex": str(ex), "message": error_message}
                    return HttpResponse(template.render(context, request))

            else:
                # TODO: make it work for text search
                print("we currently do not support faceting with text search!")
                template = loader.get_template('error.html')
                error_message = str(ex)+'\n'
                error_message += "Sorry, we currently do not support faceting with text search!"
                context = {"message": error_message}
                return HttpResponse(template.render(context, request))

            # Now if it's empty, return empty results
            if matching_docs.hits.hits == []:
                # No matching results found in this index
                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "matching_doc_ids": False,
                    "abcpattern": searchinput["pattern"],
                    "num_matching_patterns": 0 
                }
                return HttpResponse(template.render(context, request))

            # Get all the matching document ids and their facets info
            matching_doc_ids, matching_info = search_results.get_info_from_matching_docs(matching_docs)

            facets_count_dict, facet_hit_ids = search_results.count_facets_from_agg(matching_docs)

            # Get the matching doc ids with faceting
            matching_doc_ids = search_results.get_faceted_matching_ids(searchcontext, matching_doc_ids, facet_hit_ids)

            if matching_doc_ids == [] or matching_doc_ids == None:
                print("No document meets all the chosen faceting criteria...")
                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "matching_doc_ids": False,
                    "abcpattern": searchinput["pattern"],
                    "num_matching_patterns": 0 
                }
                return HttpResponse(template.render(context, request))

            # for highlighting
            matching_locations = request.session.get("matching_locations")

            # for ranking by relevancy
            match_dict_display = request.session.get("match_dict_display")

            # if a new rank method is entered TODO!!!
            if searchinput["rankby"] != False and searchinput["rankby"] != request.session["ranking_method"]:
                matching_doc_ids = search_results.re_rank_the_results(searchinput["rankby"], match_dict_display)
                # remember the new order and new rank method in request.session
                request.session["matching_doc_ids"] = matching_doc_ids
                request.session["ranking_method"] = searchinput["rankby"]

            hostname = request.get_host()
            score_info = {}
            num_matching_patterns = 0
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
                
                score_info[doc_id] = []
                score_info[doc_id].append(musicdoc.doc_type)
                #docurl = "http://"+hostname+ "/home/media/"+searchinput["index_name"]+"/"+doc_id+"/"
                docurl = "http://"+hostname+ "/home/media/"+musicdoc.index.name+"/"+doc_id+"/"

                score_info[doc_id].append(docurl)
                if musicdoc.title:
                    score_info[doc_id].append(musicdoc.title)
                else:
                    score_info[doc_id].append("Unknown title")

                if musicdoc.composer:
                    score_info[doc_id].append(musicdoc.composer.name)
                else:
                    score_info[doc_id].append("Unknown composer")

                score_info[doc_id].append(musicdoc.index.name)

                # Re-calculate the number of matching patterns
                num_matching_patterns += match_dict_display[doc_id]

            # Remember the filtered results and stats
            request.session["score_info"] = score_info
            request.session["num_matching_docs"] = len(score_info)
            request.session["num_matching_patterns"] =  num_matching_patterns
            request.session["matching_doc_ids"] = matching_doc_ids

            # Pagination for filtered view:
            callpage = request.POST.get('page', False)
            p = Paginator(tuple(score_info), settings.SCORES_PER_PAGE)
            callpage = int(callpage)
            if callpage == False or callpage == 0 or callpage == 1:
                pg = p.get_page(1)
                startfrom = 0
                endby = min(settings.SCORES_PER_PAGE , p.count)
                scores_thispg = dict(list(score_info.items())[startfrom:endby])

            context = {
                    "searchinput": searchinput,
                    "pianopattern": searchinput["pianopattern"],
                    "index_name": searchinput["index_name"],
                    "match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "num_matching_docs": len(score_info),
                    "num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    "matching_locations": matching_locations,
                    "facet_composers": facets_count_dict["composer"],
                    "facet_instruments": facets_count_dict["instrument"],
                    #"facet_keymode": facets_count_dict["keymode"],
                    #"facet_keytonicname": facets_count_dict["keytonicname"],
                    "facet_key": facets_count_dict["key"],
                    "facet_period": facets_count_dict["period"],
                    "facet_numofparts": facets_count_dict["numofparts"],
                    "facet_numofmeasures": facets_count_dict["numofmeasures"],
                    "facet_timesig": facets_count_dict["timesig"],
                    #"facet_numofnotes": facets_count_dict["numofnotes"],
                    "score_info": scores_thispg,
                    "pg": pg,
                    "startfrom": startfrom,
                    "disable_scorelib": settings.DISABLE_SCORELIB
            }

            return HttpResponse(template.render(context, request))

        elif request.method == 'GET':
            template = loader.get_template('search/filtered_result.html')
            callpage = request.GET.get('page', False)
            context = search_results.paginate_search_result(request, callpage)
            return HttpResponse(template.render(context, request))

    def DiscoveryResultView(request):

        # TODO: how about pagination? might be different from pattern search, both back and front end

        es = Elasticsearch(elastic_params)
        try:
            indices = es.indices.get_alias().keys()
        except:
            # If ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if request.method == 'POST':
            template = loader.get_template('search/discovery_result.html')

            # then read new entered facets and rank method
            searchinput = {}
            searchinput["type"] = "discovery"
            #searchinput["pattern"] = ""
            #searchinput["pianopattern"] = ""
            #searchinput["text"] = ""
            
            searchinput = search_results.read_search_input_from_request(request, searchinput)

            if "index_name" not in searchinput:
                searchinput["index_name"] = "ALL_INDICES"
            elif searchinput["index_name"] == "":
                searchinput["index_name"] = "ALL_INDICES"
            
            facets_name_list = ["composer", "period", "instrument", "key", "timesig", "numofparts", "numofmeasures"]
            request.session["facets_name_list"] = facets_name_list

            for facet_name in facets_name_list:
                searchinput[facet_name] = request.POST.get(facet_name, False)

            # get searchcontext 
            searchcontext = search_results.read_pattern_search_into_search_context(searchinput)
            
            index_wrapper = IndexWrapper(searchcontext.index)

            matching_docs = index_wrapper.search(searchcontext)
                        
            # Now if it's empty, return empty results
            if matching_docs.hits.hits == []:
                # No matching results found in this index
                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "matching_doc_ids": False,
                    "num_matching_patterns": 0 
                }
                return HttpResponse(template.render(context, request))

            # Get all the matching document ids and their facets info
            matching_doc_ids, matching_info = search_results.get_info_from_matching_docs(matching_docs)

            # for testing only
            facets_count_dict, facet_hit_ids = search_results.count_facets_from_agg(matching_docs)

            # Get the matching doc ids with faceting
            matching_doc_ids = search_results.get_faceted_matching_ids(searchcontext, matching_doc_ids, facet_hit_ids)

            if matching_doc_ids == [] or matching_doc_ids == None:
                print("No document meets all the chosen criteria...")
                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "matching_doc_ids": False,
                    "abcpattern": searchinput["pattern"],
                    "num_matching_patterns": 0 
                }
                return HttpResponse(template.render(context, request))

            # save it for pagination
            """
            matching_locations = index_wrapper.locate_matching_patterns("", matching_doc_ids, searchcontext)
            # For rank by relevancy
            match_dict_display = {}
            num_matching_patterns = 0
            for mat_doc in matching_locations:
                num_matching_patterns += mat_doc["num_occu"]
                print("There are", mat_doc["num_occu"]," matching patterns in doc id:", mat_doc["doc"])
                print("ids of all matching notes are:", mat_doc["matching_ids"], "\n")
                match_dict_display[mat_doc["doc"]] = mat_doc["num_occu"]
            
            if searchinput["rankby"] == "Relevancy":
                matching_doc_ids = sorted(match_dict_display, key=match_dict_display.get)

            if searchinput["rankby"] != False and searchinput["rankby"] != request.session["ranking_method"]:
                matching_doc_ids = search_results.re_rank_the_results(searchinput["rankby"], match_dict_display)
                # remember the new order and new rank method in request.session
                request.session["matching_doc_ids"] = matching_doc_ids
                request.session["ranking_method"] = searchinput["rankby"]

            """

            hostname = request.get_host()
            score_info = {}
            num_matching_patterns = 0
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
                
                score_info[doc_id] = []
                score_info[doc_id].append(musicdoc.doc_type)
                docurl = "http://"+hostname+ "/home/media/"+musicdoc.index.name+"/"+doc_id+"/"

                score_info[doc_id].append(docurl)
                if musicdoc.title:
                    score_info[doc_id].append(musicdoc.title)
                else:
                    score_info[doc_id].append("Unknown title")

                if musicdoc.composer:
                    score_info[doc_id].append(musicdoc.composer.name)
                else:
                    score_info[doc_id].append("Unknown composer")

                score_info[doc_id].append(musicdoc.index.name)

            # Remember the filtered results and stats

            request.session["score_info"] = score_info
            request.session["num_matching_docs"] = len(score_info)
            request.session["num_matching_patterns"] =  num_matching_patterns
            #request.session["index_name"] = searchinput["index_name"]

            # Pagination for filtered view:
            callpage = request.POST.get('page', False)
            p = Paginator(tuple(score_info), settings.SCORES_PER_PAGE)
            callpage = int(callpage)
            if callpage == False or callpage == 0 or callpage == 1:
                pg = p.get_page(1)
                startfrom = 0
                endby = min(settings.SCORES_PER_PAGE , p.count)
                scores_thispg = dict(list(score_info.items())[startfrom:endby])

            context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    #"match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "num_matching_docs": len(score_info),
                    #"num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    #"matching_locations": matching_locations,
                    "facet_composers": facets_count_dict["composer"],
                    "facet_instruments": facets_count_dict["instrument"],
                    "facet_key": facets_count_dict["key"],
                    "facet_period": facets_count_dict["period"],
                    "facet_numofparts": facets_count_dict["numofparts"],
                    "facet_numofmeasures": facets_count_dict["numofmeasures"],
                    "facet_timesig": facets_count_dict["timesig"],
                    #"facet_numofnotes": facets_count_dict["numofnotes"],
                    "score_info": scores_thispg,
                    "pg": pg,
                    "startfrom": startfrom,
                    "disable_scorelib": settings.DISABLE_SCORELIB
            }

            return HttpResponse(template.render(context, request))


    def DiscoveryFilteredResultView(request):

        es = Elasticsearch(elastic_params)
        try:
            indices = es.indices.get_alias().keys()
        except:
            # If ES is not connected, it should be warned
            template = loader.get_template('home/es_errorpage.html')
            context = {}
            return HttpResponse(template.render(context, request))

        if request.method == 'POST':
            template = loader.get_template('search/discovery_result.html')

            searchinput = {}
            searchinput["type"] = "discovery"
            #searchinput["pattern"] = ""
            #searchinput["pianopattern"] = ""
            #searchinput["text"] = ""

            searchinput = search_results.read_search_input_from_request(request, searchinput)

            if "index_name" not in searchinput:
                searchinput["index_name"] = "ALL_INDICES"
            elif searchinput["index_name"] == "":
                searchinput["index_name"] = "ALL_INDICES"
            # TODO: get index_name from request.session?

            facets_name_list = ["composer", "period", "instrument", "key", "timesig", "numofparts", "numofmeasures"]

            for facet_name in facets_name_list:
                searchinput[facet_name] = request.POST.get(facet_name, False)

            # get searchcontext 
            searchcontext = search_results.read_pattern_search_into_search_context(searchinput)
            
            index_wrapper = IndexWrapper(searchcontext.index)

            matching_docs = index_wrapper.search(searchcontext)

            # Now if it's empty, return empty results
            if matching_docs.hits.hits == []:
                # No matching results found in this index
                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "matching_doc_ids": False,
                    "num_matching_patterns": 0 
                }
                return HttpResponse(template.render(context, request))

            # Get all the matching document ids and their facets info
            matching_doc_ids, matching_info = search_results.get_info_from_matching_docs(matching_docs)

            # for testing only
            facets_count_dict, facet_hit_ids = search_results.count_facets_from_agg(matching_docs)

            # Get the matching doc ids with faceting
            matching_doc_ids = search_results.get_faceted_matching_ids(searchcontext, matching_doc_ids, facet_hit_ids)

            print("matching_doc_ids after faceting:", matching_doc_ids)

            if matching_doc_ids == [] or matching_doc_ids == None:
                print("No document meets all the chosen criteria...")
                template = loader.get_template('search/results.html')
                context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    "matching_doc_ids": False,
                    "abcpattern": searchinput["pattern"],
                    "num_matching_patterns": 0 
                }
                return HttpResponse(template.render(context, request))

            # save it for pagination
            request.session["matching_doc_ids"] = matching_doc_ids

            hostname = request.get_host()
            score_info = {}
            num_matching_patterns = 0
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
                
                score_info[doc_id] = []
                score_info[doc_id].append(musicdoc.doc_type)
                docurl = "http://"+hostname+ "/home/media/"+musicdoc.index.name+"/"+doc_id+"/"

                score_info[doc_id].append(docurl)
                if musicdoc.title:
                    score_info[doc_id].append(musicdoc.title)
                else:
                    score_info[doc_id].append("Unknown title")

                if musicdoc.composer:
                    score_info[doc_id].append(musicdoc.composer.name)
                else:
                    score_info[doc_id].append("Unknown composer")

                score_info[doc_id].append(musicdoc.index.name)

            # Remember the filtered results and stats
            request.session["score_info"] = score_info
            request.session["num_matching_docs"] = len(score_info)
            request.session["num_matching_patterns"] =  num_matching_patterns

            # Pagination for filtered view:
            callpage = request.POST.get('page', False)
            p = Paginator(tuple(score_info), settings.SCORES_PER_PAGE)
            callpage = int(callpage)
            if callpage == False or callpage == 0 or callpage == 1:
                pg = p.get_page(1)
                startfrom = 0
                endby = min(settings.SCORES_PER_PAGE , p.count)
                scores_thispg = dict(list(score_info.items())[startfrom:endby])

            context = {
                    "searchinput": searchinput,
                    "index_name": searchinput["index_name"],
                    #"match_dict_display": match_dict_display,
                    "indices_names": indices,
                    "num_matching_docs": len(score_info),
                    #"num_matching_patterns": num_matching_patterns,
                    "matching_doc_ids": matching_doc_ids,
                    #"matching_locations": matching_locations,
                    "facet_composers": facets_count_dict["composer"],
                    "facet_instruments": facets_count_dict["instrument"],
                    "facet_key": facets_count_dict["key"],
                    "facet_period": facets_count_dict["period"],
                    "facet_numofparts": facets_count_dict["numofparts"],
                    "facet_numofmeasures": facets_count_dict["numofmeasures"],
                    "facet_timesig": facets_count_dict["timesig"],
                    #"facet_numofnotes": facets_count_dict["numofnotes"],
                    "score_info": scores_thispg,
                    "pg": pg,
                    "startfrom": startfrom,
                    "disable_scorelib": settings.DISABLE_SCORELIB
            }

            return HttpResponse(template.render(context, request))
