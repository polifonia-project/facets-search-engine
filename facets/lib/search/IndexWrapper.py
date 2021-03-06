from django.conf import settings

import os

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index
from elasticsearch_dsl import Document, Integer, Text, Object, Nested, InnerDoc
from elasticsearch_dsl import Q
from elasticsearch.helpers import bulk

import json
from operator import itemgetter

from lib.music import *

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
        if auth_login is None:
            self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"], 
                                            port=settings.ELASTIC_SEARCH["port"],
                                            index=index_name)
        else:
            self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"],
                                            port=settings.ELASTIC_SEARCH["port"],
                                            index=index_name,
                                            http_auth=(auth_login, auth_password))

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

    def get_MS_from_doc(self, index_name, doc_id):

        # Get musicsummary of the given doc_id
        search = Search(using=self.elastic_search)
        search = search.params (size=settings.MAX_ITEMS_IN_RESULT)
        search = search.query("match_phrase", _id=doc_id)
        doc_info = search.execute()
        encodedMS = doc_info.hits.hits[0]['_source']['summary']

        return encodedMS
        
    def index_musicdoc(self, index_name, musicdoc, descr_dict, encodedMS):
        """ 
        Add or replace a MusicDoc in the ElasticSearch index
        """
        
        print ("Indexing MusicDoc " + musicdoc.doc_id + " in ES index: " + index_name)

        try:

            musicdoc_index = MusicDocIndex(
                meta={'id': musicdoc.doc_id, 'index': index_name},
                title = musicdoc.title, 
                composer = musicdoc.composer,
                summary = encodedMS
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
            musicdoc_index.save(using=self.elastic_search, id=musicdoc.doc_id)

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

            if search_context.is_pattern_search():
                # Get encoded MusicSummary of the current doc
                encodedMS = self.get_MS_from_doc(index_name, doc_id)

                # Decode MusicSummary
                msummary = MusicSummary()
                msummary.decode(encodedMS)

                pattern_sequence = search_context.get_pattern_sequence()

                if search_context.search_type == settings.EXACT_SEARCH:
                    mirror_setting = False
                    count_match_for_exact_search+=1
                    all_occurrences = msummary.find_exact_matches(pattern_sequence, search_context.search_type)

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
                matching_ids = msummary.find_matching_ids(pattern_sequence, search_context.search_type, search_context.mirror_search)

            #elif search_context.is_text_search():
                '''
                Wait for scores to be saved...
                TODO: Get IDs of matching M21 objects from the scores.
                
                #Instead of getting MusicSummary and locate the pattern when the search type is pattern search, 
                #here we directly get scores from the opus that match in the search,
                #and find if the text is in the lyrics of the opus.
    
                best_occurrence = ""
                #always "" in text search mode because best occu is supposed to be a pattern sequence
                distance = 0
                #No distance measurement in this search mode
                num_occu = 0

                matching_ids = []
                #IDs of matching M21 objects
                score = opus.get_score()
                #Find the matching id by locating searched text in the score
                for voice in score.get_all_voices():
                    #get lyrics of the current voice
                    curr_lyrics = voice.get_lyrics()
                    if curr_lyrics != None:
                        if search_context.text in curr_lyrics:
                            #There is a match within the current lyrics
                            occurrences, curr_matching_ids = voice.search_in_lyrics(search_context.text)
                            if occurrences > 0:
                                # add to total number of occurrences
                                num_occu += occurrences
                                #If there is a match
                                print("Found occurrence in opus_id:  ", opus.id)
                                print("Appeared in voice: ", voice.id, ", occurrences: ", occurrences)
                                for m_id in curr_matching_ids:
                                    matching_ids.append(m_id)
                '''
            opera.append({"doc": doc_id, "matching_ids": json.dumps(matching_ids), "num_occu": num_occu, "distance": distance, "best_occurrence": str(best_occurrence)})

        return opera

    def search(self, search_context):
        '''
        Search function: sends a combined query to ElasticSearch
        '''
        pattern_sequence = search_context.get_pattern_sequence()
        """
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
        
        search = Search(using=self.elastic_search)
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
        if search_context.pattern != '':
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
