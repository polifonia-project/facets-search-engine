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

@csrf_exempt
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

            searchinput["type"] = request.POST.get('searchtype', False)
            # The search type names for ES should be all in lower case
            searchinput["type"] = searchinput["type"].lower()

            searchinput["index_name"] = request.POST.get('indexname', False)
            # TO-DO: Forcing index_name to be all lower case might cause error.
            # Find a better fix: do not put the first letter as captial letter when displaying/send through request
            searchinput["index_name"] = searchinput["index_name"].lower()

            searchinput["composer"] = request.POST.get('composer', False)

            if searchinput["pattern"]:
                #print(searchinput)
                searchcontext = SearchContext()
                # json -> searchcontext
                searchcontext.read(searchinput)
                # print the content of SearchContext object
                print("\n\nSearching in index: ", searchcontext.index)
                print("Search type: ", searchcontext.search_type)
                if searchcontext.pattern:
                    print("ABC encoded pattern: ", searchcontext.pattern)
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


                """
                # if there is a list of selected composers, filter the matching docs:
                if searchinput["composer"] != [] and searchinput["composer"] != False:
                    for hit in matching_docs.hits.hits:
                        if 'composer' in hit['_source']:
                            if hit['_source']['composer'] in searchinput["composer"]:
                                matching_doc_ids.append(hit['_id'])
                                matching_composers.append()
                """
                
                print("Matching documents are:", matching_doc_ids)
                print("Matching composers are:", matching_composers)

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

@csrf_exempt
def HighlightMusicDocView(request, index_name, doc_id):
    # Highlight patterns while viewing a music document

    #TODO: get search context from def results
    """
    if request.method == 'GET': # or POST, since it is searching?
        try:
            # get it from search??
            # highlight_ids = matching_locations[doc_id]["matching_ids"]
        except Exception as ex:
            print("Error occurred while getting ids to highlight:", str(ex))
    """
    template = loader.get_template('search/highlight_musicdoc.html')
    # TODO: this highlight_musicdoc.html needs to be written
    context = {
        "index_name": index_name, 
        "doc_id": doc_id,
        "highlight_ids": highlight_ids}

    return HttpResponse(template.render(context, request))



# The following are from Neuma for MusicDocView
#class OpusView(NeumaView):
    
    def get_context_data(self, **kwargs):
        # Get the opus
        opus_ref = self.kwargs['opus_ref']

        opus = Opus.objects.get(ref=opus_ref)

        # Initialize context
        context = super(OpusView, self).get_context_data(**kwargs)

        # Record the opus as the contextual one
        self.request.session["search_context"].ref = opus.ref
        self.request.session["search_context"].type = settings.OPUS_TYPE

        # By default, the tab shown is the first one (with the score)
        context['tab'] = 0
        #initialize ?
        context["matching_ids"] = ""

        # The pattern: it comes either from the search form (and takes priority)
        # or from the session

        #NOT necessary because the keyword is already saved in self.request.session["search_context"].keywords
        #self.request.GET and self.request.POST are empty
        """
        #lyrics search are not available yet
        if self.request.session["search_context"].keywords != "":
            #There is a keyword to search
            matching_ids = []
            keyword_in_search = self.request.session["search_context"].keywords
            score = opus.get_score()
            for voice in score.get_all_voices():
                #get lyrics of the current voice
                curr_lyrics = voice.get_lyrics()
                if curr_lyrics != None:
                    #There is a match within the current lyrics
                    if keyword_in_search in curr_lyrics:
                        occurrences, curr_matching_ids = voice.search_in_lyrics(keyword_in_search)
                        if occurrences > 0:
                            for m_id in curr_matching_ids:
                                matching_ids.append(m_id)
            context["pattern"] = ""
            #Could be improved if necessary: context["occurrences"] in the same format as what it is for pattern search,
            #speicifying the voices and occurrences in each voices instead of a total number of occurrences
            context["occurrences"] = len(matching_ids)
            context["matching_ids"] = mark_safe(json.dumps(matching_ids))
        """
        # Looking for the pattern if any
        if self.request.session["search_context"].pattern != "":
            pattern_sequence = Sequence()
            pattern_sequence.set_from_pattern(self.request.session["search_context"].pattern)

            msummary = MusicSummary()
            if opus.summary:
                with open(opus.summary.path, "r") as summary_file:
                    msummary_content = summary_file.read()
                msummary.decode(msummary_content)
            else:
                logger.warning ("No summary for Opus " + opus.ref)

            search_type = self.request.session["search_context"].search_type
            mirror_setting = self.request.session["search_context"].mirror_search

            occurrences = msummary.find_positions(pattern_sequence, search_type, mirror_setting)
            matching_ids = msummary.find_matching_ids(pattern_sequence, search_type, mirror_setting)
            
            context["msummary"] = msummary
            context["pattern"] = self.request.session["search_context"].pattern
            context["occurrences"] = occurrences
            context["matching_ids"] = mark_safe(json.dumps(matching_ids))
        
        # Analyze the score
        score = opus.get_score()
        context["opus"] = opus
        context["score"] = score
        """
        # get meta values 
        context["meta_values"] = opus.get_metas()
        
        # Get the measure for which neighbors must be shown
        if 'sim_measure' in self.request.GET:
            context['measure'] = self.request.GET['sim_measure']
            # We show the second tab
            context['tab'] = 2
        else:
            # Default
            context['measure'] = 'pitches'
        
        """
        # Show detail on the sequence and matching
        if "explain" in self.request.GET:
            context["explain"] = True
        else:
            context["explain"] = False

        return context
        #return render(request, "home/musicdoc.html", context) ???
    #return HttpResponse("Display music doc without search result")
    
