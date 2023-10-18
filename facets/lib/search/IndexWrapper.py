from django.conf import settings

import os
from attributedict.collections import AttributeDict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index
from elasticsearch_dsl import Document, Integer, Text, Object, Nested, InnerDoc
from elasticsearch_dsl import Q
from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl import UpdateByQuery
from elasticsearch.helpers import bulk

import json
from operator import itemgetter

from lib.music import *
from lib.music.MusicSummary import MusicSummary

from rest import models
from lib.search.Sequence import Sequence

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexWrapper:
    """
    
    A class to index music documents and send queries to ElasticSearch
    
    This class acts as a proxy for all queries sent to ElasticSearch. 
    It relies on the ``elasticsearch_dsl`` package, documented here:
    https://elasticsearch-dsl.readthedocs.io/en/latest/. 
    
    """

    def __init__(self, index_name, auth_login=None, auth_password=None) :
        """
           Connect to the ElasticSearch server, and open the index
        """
        hp = getattr(settings, "ELASTIC_SEARCH", "localhost")["hosts"][0]
        elastic_params = "http://"+hp["host"]+":"+str(hp["port"])
        if auth_login is None:
            if index_name != "ALL_INDICES" and index_name != "" and index_name != "Not selected":
                # self.elastic_search = Elasticsearch(hosts=[ {'host': host, 'port': port}, ], index=index_name)
                self.elastic_search = Elasticsearch(elastic_params)
            else:
                # if not specified, search in all indices
                self.elastic_search = Elasticsearch(elastic_params)
        else:
            """
            self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"],
                                            port=settings.ELASTIC_SEARCH["port"],
                                            index=index_name,
                                            http_auth=(auth_login, auth_password))
            """
            if index_name != "ALL_INDICES" and index_name != "":
                self.elastic_search = Elasticsearch(hosts=[ {'host': host, 'port': port}, ], 
                                            index=index_name,
                                            http_auth=(auth_login, auth_password))
            else:
                self.elastic_search = Elasticsearch(hosts=[ {'host': host, 'port': port}, ],
                                            index="_all",
                                            http_auth=(auth_login, auth_password))

        if index_name != "ALL_INDICES" and index_name != "":
            # Open, and possibly create the index
            self.index = Index(index_name, using=self.elastic_search)
            
            if not self.index.exists(using=self.elastic_search):
                # Create the index
                self.index.create(using=self.elastic_search)
                self.index.settings(number_of_shards=1, number_of_replicas=0)

            self.index.open(using=self.elastic_search)

            # Directory containing some pre-defined queries in JSON
            #self.query_dir = settings.ES_QUERY_DIR
        
    def get_index_info(self):
        '''
        Obtain main infos on the index
        '''
        return self.index.get()

    def get_facet_for_initial_navigation(self, index_name):

        if index_name == "ALL_INDICES":
            print("Showing facets in all indices on discovery page.")
            search = Search(using=self.elastic_search, index="_all")
        else:
            print("Showing facets in ",index_name, "on discovery page.")
            search = Search(using=self.elastic_search, index=index_name)

        #search = search.params(size=settings.MAX_ITEMS_IN_RESULT)
        search = search.extra(track_total_hits=True)
        search = search.query("match_all")

        search.aggs.bucket('per_composer', 'terms', field='composer.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_instrument', 'terms', field='infos.instruments.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        #search.aggs.bucket('per_keytonicname', 'terms', field='infos.key_tonic_name.keyword').metric('top_hits', 'terms', field = '_id', size=1000)
        #search.aggs.bucket('per_keymode', 'terms', field='infos.key_mode.keyword').metric('top_hits', 'terms', field = '_id', size=1000)
        search.aggs.bucket('per_key', 'terms', field='infos.key.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_period', 'terms', field='infos.period.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_parts', 'terms', field='infos.num_of_parts').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_measures', 'terms', field='infos.num_of_measures').metric('top_hits', 'terms', field = '_id', size=100000)
        #search.aggs.bucket('per_notes', 'terms', field='infos.num_of_notes').metric('top_hits', 'terms', field = '_id', size=1000)
        search.aggs.bucket('per_timesig', 'terms', field='infos.initial_time_signature.keyword').metric('top_hits', 'terms', field = '_id', size=100000)

        # just for testing..
        logger.info ("Search doc sent to ElasticSearch: " + str(search.to_dict()))
        print ("Search doc sent to ElasticSearch: " + str(search.to_dict()).replace("'", "\""))

        matching_docs = search.execute() #scan does not work for aggs.
        return matching_docs

    def navigate_with_facets(self, index_name):

        if index_name == "ALL_INDICES" or index_name == "" or index_name == "Not selected" or index_name == "not selected" or index_name == False:
            search = Search(using=self.elastic_search)
        else:
            search = Search(using=self.elastic_search, index=index_name)
        search = search.params (size=settings.MAX_ITEMS_IN_RESULT)
        search = search.extra(track_total_hits=True)

        search.aggs.bucket('per_composer', 'terms', field='composer.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_instrument', 'terms', field='infos.instruments.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        #search.aggs.bucket('per_keytonicname', 'terms', field='infos.key_tonic_name.keyword').metric('top_hits', 'terms', field = '_id', size=1000)
        #search.aggs.bucket('per_keymode', 'terms', field='infos.key_mode.keyword').metric('top_hits', 'terms', field = '_id', size=1000)
        search.aggs.bucket('per_key', 'terms', field='infos.key.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_period', 'terms', field='infos.period.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_parts', 'terms', field='infos.num_of_parts').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_measures', 'terms', field='infos.num_of_measures').metric('top_hits', 'terms', field = '_id', size=100000)
        #search.aggs.bucket('per_notes', 'terms', field='infos.num_of_notes').metric('top_hits', 'terms', field = '_id', size=1000)
        search.aggs.bucket('per_timesig', 'terms', field='infos.initial_time_signature').metric('top_hits', 'terms', field = '_id', size=100000)

        # just for testing..
        logger.info ("Search doc sent to ElasticSearch: " + str(search.to_dict()))
        print ("Search doc sent to ElasticSearch: " + str(search.to_dict()).replace("'", "\""))

        matching_docs = search.execute()

        return matching_docs

    def get_all_composer_names(self):
        '''
        Get ALL composer names in ALL indexes
        '''
        composer_names = []
        search = Search(using=self.elastic_search)
        search = search.params (size=settings.MAX_ITEMS_IN_RESULT)

        search = search.query("match_all")
        doc_info = search.execute()

        for doc in doc_info.hits.hits:
            if 'composer' in doc['_source']:
                if doc['_source']['composer'] not in composer_names:
                    composer_names.append(doc['_source']['composer'])

        # Remove duplicates and get the final list of composers
        invalid_name = [""] # could be more than "" here
        composer_names = list(set(composer_names)-set(invalid_name))

        return composer_names
    
    """
    def get_all_instrument_names(self):
        '''
        Get ALL composer names in ALL indexes
        '''

        instrument_names = []
        search = Search(using=self.elastic_search)
        search = search.params (size=settings.MAX_ITEMS_IN_RESULT)
        search = search.query("match_all")
        doc_info = search.execute()

        for doc in doc_info.hits.hits:
            if 'infos' in doc['_source']:
                if doc['_source']['infos']["instruments"] != None and doc['_source']['infos']["instruments"] != []:
                    for instrument_name in doc['_source']['infos']["instruments"]:
                        if instrument_name not in instrument_names:
                            instrument_names.append(instrument_name)

        # Remove duplicates and get the final list of composers
        invalid_name = [""] # cou ld be more than "" here
        instrument_names = list(set(instrument_names)-set(invalid_name))

        return instrument_names
    """

    def get_source_from_doc(self, index_name, doc_id):
        search = Search(using=self.elastic_search)
        search = search.query("match_phrase", _id=doc_id)
        doc_info = search.execute()
        return doc_info.hits.hits[0]['_source']

    def get_MS_from_doc(self, index_name, doc_id):
        # Get MS of the doc

        search = Search(using=self.elastic_search)
        search = search.query("match_phrase", _id=doc_id)
        doc_info = search.execute()
        if 'summary' in doc_info.hits.hits[0]['_source']:
            encodedMS = doc_info.hits.hits[0]['_source']['summary']
            return encodedMS
        else:
            return None

    def get_info_from_doc(self, index_name, doc_id):
        # Get info of the doc

        search = Search(using=self.elastic_search)
        search = search.query("match_phrase", _id=doc_id)
        doc_info = search.execute()
        if 'infos' in doc_info.hits.hits[0]['_source']:
            extracted_infos = doc_info.hits.hits[0]['_source']['infos']
            return extracted_infos.to_dict()
        else:
            return None

    def get_descriptor_from_doc(self, index_name, doc_id):
        # Get descriptor of the doc

        search = Search(using=self.elastic_search)
        search = search.query("match_phrase", _id=doc_id)
        doc_info = search.execute()
        
        descr_dict = {}
        if 'chromatic' in doc_info.hits.hits[0]['_source']:
            descr_dict["chromatic"] = doc_info.hits.hits[0]['_source']['chromatic']
        if 'diatonic' in doc_info.hits.hits[0]['_source']:
            descr_dict["diatonic"] = doc_info.hits.hits[0]['_source']['diatonic']
        if 'rhythm' in doc_info.hits.hits[0]['_source']: 
            # note that it's "rhythm" on ES, not rhythmic
            descr_dict["rhythmic"] = doc_info.hits.hits[0]['_source']['rhythm'] 
        if 'notes' in doc_info.hits.hits[0]['_source']:
            descr_dict["notes"] = doc_info.hits.hits[0]['_source']['notes']
        if 'lyrics' in doc_info.hits.hits[0]['_source']:
            descr_dict["lyrics"] = doc_info.hits.hits[0]['_source']['lyrics']

        temp_dict = doc_info.hits.hits[0]['_source'].to_dict()

        return temp_dict

    def update_musicdoc_metadata(self, index_name, doc_id, musicdoc):
        
        # todo for templates: there should be an option for updating all the doc_id in all indexes in UI "all above"

        # get the stored MS
        encodedMS = self.get_MS_from_doc(index_name, doc_id)
        dict_info = self.get_info_from_doc(index_name, doc_id)
        # add some other metainfo
        dict_info["title"] = musicdoc.title
        if musicdoc.composer != "" and musicdoc.composer != None:
            dict_info["composer"] = musicdoc.composer.name
            if musicdoc.composer.period != "" and musicdoc.composer.period != None:
                dict_info["period"] = musicdoc.composer.period
                print("Updating period info to ES")

        extracted_infos = AttributeDict(dict_info)
        musicdoc_index = MusicDocIndex(
                meta={
                    'id': musicdoc.doc_id,
                    'index': index_name,
                },
                title = musicdoc.title, 
                composer = musicdoc.composer.name,
                summary = encodedMS,
                infos = extracted_infos
        )
        descr_dict = self.get_descriptor_from_doc(index_name, doc_id)
        musicdoc_index.preserve_descriptor(descr_dict)

        # Save the updated index
        musicdoc_index.save(using=self.elastic_search, index=index_name, id=doc_id)

        return

    def index_musicdoc(self, index_name, musicdoc, descr_dict, encodedMS, extracted_infos):
        """ 
        Add or replace a MusicDoc in the ElasticSearch index
        """
        
        print ("Indexing MusicDoc " + musicdoc.doc_id + " in ES index: " + index_name)

        try:

            musicdoc_index = MusicDocIndex(
                meta={
                    'id': musicdoc.doc_id,
                    'index': index_name,
                },
                #TODO: where to put title and composer and all these info? within meta or not?
                title = musicdoc.title, 
                composer = musicdoc.composer.name,
                summary = encodedMS,
                infos = extracted_infos
            )

            """
            # Iterate over types of descriptors in the dictionary
            # For example, descr_dict["chromatic"]["P1-1"]["value"] contains the chromatic descriptor of voice P1-1 of the doc
            for descr_type in descr_dict:
                #Iterate over parts in one type of descriptor
                for voice_id in descr_dict[descr_type]:
                    part_id = descr_dict[descr_type][voice_id]["part"]
                    voice_id = descr_dict[descr_type][voice_id]["voice"]
                    descr_value = descr_dict[descr_type][voice_id]["value"]
            """

            # Add/update descriptors(a.k.a. features) to ES index
            musicdoc_index.add_descriptor(descr_dict)

            # Save the updated index
            musicdoc_index.save(using=self.elastic_search, index=index_name, id=musicdoc.doc_id)

        except Exception as ex:
            print ("Error occurred while trying to index: " + str(ex))
        
        return

    def locate_matching_patterns(self, index_name, matching_doc_ids, search_context):

        """
            Locate every matching patterns in the music document,
            and rank the results by melodic or rhythmic distance.
        """

        opera = []
        for doc_id in matching_doc_ids:
            matching_ids = []
            distance = 0
            best_occurrence = None
            all_occurrences = 0

            if search_context.is_pattern_search():
                
                # Get encoded MusicSummary of the current doc
                encodedMS = self.get_MS_from_doc(index_name, doc_id)
                
                # Make sure the MusicSummary of this doc is on ES index, otherwise there is no way to locate
                if encodedMS == None:
                    print("Can not find MusicSummary of this document on ES, please re-index:", doc_id)
                    continue

                # Decode MusicSummary
                msummary = MusicSummary()
                msummary.decode(encodedMS)

                pattern_sequence = search_context.get_pattern_sequence()

                if search_context.search_type == settings.EXACT_SEARCH:
                    mirror_setting = False
                    count_match_for_exact_search+=1
                    all_occurrences = msummary.find_exact_matches(pattern_sequence, search_context.search_type)
                    num_occu = len(all_occurrences)

                if search_context.search_type == settings.CHROMATIC_SEARCH or search_context.search_type == settings.DIATONIC_SEARCH or search_context.search_type == settings.RHYTHMIC_SEARCH:
                    #return the sequences that match and the distances
                    mirror_setting = search_context.is_mirror_search()

                    """
                        Find the occurrences of matches within the opus, 
                        and measure the melodic or rhythmic distance depending on context.
                        If there is more than one match in an opus,
                        we only take the distance between the best match(with least distance with the query)
                        "best_occurrence" here should be a pattern sequence.
                    """
                    all_occurrences, best_occurrence, distance = msummary.get_best_occurrence(pattern_sequence, search_context.search_type, mirror_setting)

                    num_occu = len(all_occurrences)
                    logger.info ("Found best occurrence : " + str(best_occurrence) + " with distance " + str(distance))

                # Locate ids of all matching patterns to highlight
                occloc, matching_ids = msummary.find_matching_ids(pattern_sequence, search_context.search_type, search_context.mirror_search)


            elif search_context["pianopattern"] == "" and search_context["pattern"] == "" and search_context["text"] == "":
                #search_context.search_type == "Discovery":
                if MusicDoc.objects.filter(doc_id=doc_id).exists():
                        curr_musicdoc = MusicDoc.objects.filter(doc_id=doc_id)
                        matching_ids = []
                        num_occu = 1
                        distance = 0
                        best_occurrence = ""
                else:
                        print("Couldn't find the matching musicdoc in database, thus skipping it.")
                        continue

            #elif search_context.is_text_search():
                '''
                Once the scores are saved...
                TODO1: Make it work for all types of scores by adding codes to Voice.py or something else
                TODO: Get IDs of matching M21 objects from the scores.
                
                #Instead of getting MusicSummary and locate the pattern when the search type is pattern search, 
                #here we directly get scores from the opus that match in the search,
                #and find if the text is in the lyrics of the opus.
    
                # "" in text search mode because best occu is supposed to be a pattern sequence
                best_occurrence = ""
                # No distance measurement in this search mode
                distance = 0
                # To be calculated
                num_occu = 0
                
                try:
                # Create a Score object
                    score = Score()
                    # Get a Score object from m21stream of the score. 
                    score.load_component(m21_score)

                if MusicDoc.objects.filter(doc_id=doc_id).exists():
                    curr_musicdoc = MusicDoc.objects.filter(doc_id=doc_id)
                else:
                    print("Couldn't find the matching musicdoc in database, thus skipping it.")
                    continue

                #GET VOICE instead of MUSICDOC
                
                score = Score()
                score.load_component(m21_score)#something like this

                # IDs of matching M21 objects
                matching_ids = []
                score = opus.get_score()
                """
                # in the original neuma code it was like this:
                    def get_score(self):
                    #Get a score object from an XML document
                        score = Score()
                        # Try to obtain the MEI document, which contains IDs
 
                        if self.mei :
                            #print ("Load from MEI")
                            score.load_from_xml(self.mei.path, "mei")
                            return score
                        elif self.musicxml :
                            #print ("Load from MusicXML")
                            score.load_from_xml(self.musicxml.path, "musicxml")
                            return score
                        else:
                            raise LookupError ("Opus " + self.ref + " doesn't have any XML file attached")
                """
                # Find the matching id by locating searched text in the score
                for voice in score.get_all_voices():
                    #get lyrics of the current voice
                    curr_lyrics = voice.get_lyrics()
                    if curr_lyrics != None:
                        if search_context.text in curr_lyrics:
                            # There is a match within the current lyrics
                            occurrences, curr_matching_ids = voice.search_in_lyrics(search_context.text)
                            if occurrences > 0:
                                # Add to total number of occurrences
                                num_occu += occurrences
                                # if there is a match, we may print:
                                #print("Found occurrence in opus_id:  ", opus.id)
                                #print("Appeared in voice: ", voice.id, ", occurrences: ", occurrences)
                                for m_id in curr_matching_ids:
                                    matching_ids.append(m_id)
                '''

            opera.append({"doc": doc_id, "matching_ids": json.dumps(matching_ids), "occloc": occloc, "num_occu": num_occu, "distance": distance, "best_occurrence": str(best_occurrence)})

        return opera

    def search(self, search_context):
        '''
        Search function: sends a combined query to ElasticSearch
        '''
        pattern_sequence = search_context.get_pattern_sequence()
        """
        # for testing
        print("Search " 
               + "  Text: '" + search_context.text + "'"
               + "'  Pattern Sequence: [" + str(pattern_sequence) + "]")
        """
        
        # Get search query
        search = self.get_search(search_context)

        logger.info ("Search doc sent to ElasticSearch: " + str(search.to_dict()))
        print ("Search doc sent to ElasticSearch: " + str(search.to_dict()).replace("'", "\""))

        # Get matching results from Elasticsearch
        matching_docs = search.execute()

        return matching_docs

    def get_search(self, search_context):
        """
        Create the search object with ElasticSearch DSL
        """
        
        search = Search(using=self.elastic_search, index=search_context.index)
        search = search.params (size=settings.MAX_ITEMS_IN_RESULT)

        # If there is text content to search in lyrics
        if search_context.text != '':
            # TODO: need to test if it works for both composer, title and lyrics
            q_title = Q("multi_match", query=search_context.text, fields=['lyrics', 'composer', 'title'])
            # Searching for the requested text in lyrics
            q_lyrics = Q("match_phrase", lyrics__value=search_context.text)
            # Combine the search
            search = search.query(q_title | q_lyrics)
        # If there is a pattern to search

        if search_context.pattern != '' or search_context.pianopattern != '':
            if search_context.search_type == settings.RHYTHMIC_SEARCH:
                search = search.query("match_phrase", rhythm__value=search_context.get_rhythmic_pattern())

            elif search_context.search_type == settings.CHROMATIC_SEARCH:
                # If mirror search mode is on, search the mirror patterns too.
                if search_context.is_mirror_search() == True:
                    # calling get_chromatic_pattern function returns a tuple of 2 lists here
                    mel_patterns = search_context.get_chromatic_pattern(True)
                    og_patterns = mel_patterns[0]
                    mr_patterns = mel_patterns[1]
                    # Search for the original patterns
                    q_og = Q("match_phrase", chromatic__value=og_patterns)
                    # Search for the mirror patterns
                    q_mr = Q("match_phrase", chromatic__value=mr_patterns)
                    # Combine the search
                    search = search.query(q_og | q_mr)
                else:
                    # Otherwise only search for the original chromatic patterns
                    search = search.query("match_phrase", chromatic__value=search_context.get_chromatic_pattern())

            elif search_context.search_type == settings.DIATONIC_SEARCH:
                # If mirror search mode is on
                if search_context.is_mirror_search() == True:
                    # dia_patterns includes two lists, a list of original patterns and a list of mirror patterns
                    dia_patterns = search_context.get_diatonic_pattern(True)
                    # original patterns
                    og_patterns = dia_patterns[0]
                    # mirror patterns
                    mr_patterns = dia_patterns[1]
                    q_og = Q("match_phrase", diatonic__value=og_patterns)
                    q_mr = Q("match_phrase", diatonic__value=mr_patterns)
                    search = search.query(q_og | q_mr)
                else:
                    # Otherwise only search for the original diatonic patterns
                    search = search.query("match_phrase", diatonic__value=search_context.get_diatonic_pattern())

            elif search_context.search_type == settings.EXACT_SEARCH:
                search = search.query("match_phrase", notes__value=search_context.get_notes_pattern())
        
        if search_context.pattern == '' and search_context.text == '' and search_context.pianopattern == '':
            # Discovery mode
            # search in all indices
            if search_context.index == '' or search_context.index == "ALL_INDICES":
                search = Search(using=self.elastic_search)
            else:
                # search in chosen index
                search = Search(using=self.elastic_search, index=search_context.index)
            search = search.params (size=settings.MAX_ITEMS_IN_RESULT)
            
            # Only allow selection of one facet in the beginning! 
            # initialize q, if no facet is selected then send a "match_all"
            q = Q("match_all")
            if search_context.facet_composers != "":
                q = Q("multi_match", query=search_context.facet_composers, fields=['composer.keyword'])
            if search_context.facet_instruments != "":
                q = Q("multi_match", query=search_context.facet_instruments, fields=['infos.instruments.keyword'])
            if search_context.facet_key != "":
                q = Q("multi_match", query=search_context.facet_key, fields=['infos.key.keyword'])
            if search_context.facet_numofparts != "":
                q = Q("multi_match", query=search_context.facet_numofparts, fields=['infos.num_of_parts'])
            if search_context.facet_numofmeasures != "":
                q = Q("multi_match", query=search_context.facet_numofmeasures, fields=['infos.num_of_measures'])
            if search_context.facet_period != "":
                q = Q("multi_match", query=search_context.facet_period, fields=['infos.period.keyword'])
            if search_context.facet_timesig != "":
                q = Q("multi_match", query=search_context.facet_timesig, fields=['infos.initial_time_signature.keyword'])

            search = search.query(q)
            # search with facets

        #print("***** FACETING")
        #print("==========================")
        search.aggs.bucket('per_composer', 'terms', field='composer.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_instrument', 'terms', field='infos.instruments.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        #search.aggs.bucket('per_keytonicname', 'terms', field='infos.key_tonic_name.keyword').metric('top_hits', 'terms', field = '_id', size=1000)
        #search.aggs.bucket('per_keymode', 'terms', field='infos.key_mode.keyword').metric('top_hits', 'terms', field = '_id', size=1000)
        search.aggs.bucket('per_period', 'terms', field='infos.period.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_key', 'terms', field='infos.key.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_parts', 'terms', field='infos.num_of_parts').metric('top_hits', 'terms', field = '_id', size=100000)
        search.aggs.bucket('per_measures', 'terms', field='infos.num_of_measures').metric('top_hits', 'terms', field = '_id', size=100000)
        #search.aggs.bucket('per_notes', 'terms', field='infos.num_of_notes').metric('top_hits', 'terms', field = '_id', size=1000)
        search.aggs.bucket('per_timesig', 'terms', field='infos.initial_time_signature.keyword').metric('top_hits', 'terms', field = '_id', size=100000)
        # and so on...

        return search

class DescriptorIndex(InnerDoc):
    '''
     Encoding of a specific descriptor for a voice, stored in ElasticSearch
     
     A descriptor is a character string that encodes a specific aspect (rhythm, melody, lyrics)
     of a voice in a music piece. Its structure (sequence of n-grams) is such that effective text-based search
     supported by ElasticSearch can be carried out on its content.
    '''
    # To improve: we do not need to save part info in ES if it's all "all parts", but this info could be kept in MS.
    #part = Text()
    voice = Text()
    value = Text()

class MusicDocIndex(Document):
    '''
     Encoding of informations related to a MusicDoc, stored in ElasticSearch
    '''
    id = Text()
    index = Text()

    title = Text()
    composer = Text()
    
    summary = Text()

    infos = Text()

    # N-gram encoding of the chromatic intervals
    chromatic = Nested( 
        doc_class=DescriptorIndex,
    )
    # N-gram encoding of the diatonic intervals
    diatonic = Nested(
        doc_class=DescriptorIndex,
    )
    # N-gram encoding of the rhythm intervals
    rhythm = Nested(
        doc_class=DescriptorIndex,
    )
    # Ngram encoding of the notes for exact search
    notes = Nested(
        doc_class=DescriptorIndex,
    )
    # Text encoding of the lyrics
    lyrics = Nested(
        doc_class=DescriptorIndex,
    )

    def add_descriptor(self, descr_dict):
        for voice_id in descr_dict["chromatic"]:
            self.chromatic.append(descr_dict["chromatic"][voice_id])
        for voice_id in descr_dict["diatonic"]:
            self.diatonic.append(descr_dict["diatonic"][voice_id])
        for voice_id in descr_dict["rhythmic"]:
            self.rhythm.append(descr_dict["rhythmic"][voice_id])
        for voice_id in descr_dict["notes"]:
            self.notes.append(descr_dict["notes"][voice_id])
        for voice_id in descr_dict["lyrics"]:
            self.lyrics.append(descr_dict["lyrics"][voice_id])

    def preserve_descriptor(self, descr_dict):

        if 'chromatic' in descr_dict:
            for dict_voice in descr_dict["chromatic"]:
                self.chromatic.append(dict_voice)
            #voice_id = dict_voice['voice']
            #print(voice_id)
            #print(dict_voice['value'])
        if 'diatonic' in descr_dict:
            for dict_voice in descr_dict["diatonic"]:
                self.diatonic.append(dict_voice)

        if "rhythm" in descr_dict:
            for dict_voice in descr_dict["rhythm"]:
                self.rhythm.append(dict_voice)

        if "notes" in descr_dict:
            for dict_voice in descr_dict["notes"]:
                self.notes.append(dict_voice)

        if "lyrics" in descr_dict:
            for dict_voice in descr_dict["lyrics"]:
                self.lyrics.append(dict_voice)
