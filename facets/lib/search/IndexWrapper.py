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

#from manager.models import Opus
#from search.Sequence import Sequence

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexWrapper:
    """
    
    A class to send NEUMA-specific queries to ElasticSearch
    
    This class acts as a proxy for all queries sent to ElasticSearch. It relies on
    the ``elasticsearch_dsl`` package, documented here:
    https://elasticsearch-dsl.readthedocs.io/en/latest/. 
    
    """

    def __init__(self, auth_login=None, auth_password=None) :
        """
           Connect to the ElasticSearch server, and open the index
        """
        if auth_login is None:
            self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"], 
                                            port=settings.ELASTIC_SEARCH["port"],
                                            index=settings.ELASTIC_SEARCH["index"])
        else:
            self.elastic_search = Elasticsearch(host=settings.ELASTIC_SEARCH["host"], 
                                            port=settings.ELASTIC_SEARCH["port"],
                                            index=settings.ELASTIC_SEARCH["index"],
                                            http_auth=(auth_login, auth_password))
            
        # Open, and possibly create the index
        self.index = Index (settings.ELASTIC_SEARCH["index"],using=self.elastic_search)
        
        if not self.index.exists(using=self.elastic_search):
            # Create the index
            self.index.create(using=self.elastic_search)
            self.index.settings(number_of_shards=1, number_of_replicas=0)

        self.index.open(using=self.elastic_search)
        #: Directory containing some pre-defined queries in JSON
        self.query_dir = settings.ES_QUERY_DIR
        
    
    def get_index_info (self):
        '''
        Obtain main infos on the index
        '''
        return self.index.get()

    def index_opus (self, opus):
        """ 
        Add of replace an Opus in the ElasticSeaerch index
        
        """
        
        print ("Index Opus " + opus.ref)
        # First time that we index this Opus
        try:
            score = opus.get_score()
            # CHANGE: we do not longer store the summary in ES
            #music_summary = score.get_music_summary()
            #music_summary.opus_id = opus.ref
            #msummary_for_es = music_summary.encode()

            opus_index = OpusIndex(
                meta={'id': opus.ref, 'index': settings.ELASTIC_SEARCH["index"]},
                corpus_ref=opus.corpus.ref,
                ref=opus.ref,
                #summary = msummary_for_es,
                title=opus.title,
                composer=opus.composer,
                lyricist=opus.lyricist,
            )
            
            # Add descriptors to opus index
            for descriptor in opus.descriptor_set.all():
                #print ("Add descriptor for voice " + descriptor.voice, " type " + descriptor.type)
                opus_index.add_descriptor(descriptor)
            # Saving the opus_index object triggers insert or replacement in ElasticSearch
            opus_index.save(using=self.elastic_search,id=opus.ref)

        except Exception as ex:
            print ("Error met when trying to index: " + str(ex))
            #When the analysis finish, no value would be assigned to mel_pat_dict etc.. thus simply return void
        
        return

        # Add descriptors to opus index
        for descriptor in opus.descriptor_set.all():
            #print ("Add descriptor for voice " + descriptor.voice, " type " + descriptor.type)
            opus_index.add_descriptor(descriptor)

        # Saving the opus_index object triggers insert or replacement in ElasticSearch
        opus_index.save(using=self.elastic_search,id=opus.ref)

class DescriptorIndex(InnerDoc):
    '''
     Encoding of a specific descriptor for a voice, stored in ElasrticSearch
     
     A descriptor is a character string that encodes a specific aspect (rhythm, melody, lyrics)
     of a voice in a music piece. Its structure (sequence of ngrams) is such that effective text-based search
     supported by ElasticSearch can be carried out on its content.
    '''
    
    part = Text()
    voice = Text()
    value = Text()

class OpusIndex(Document):
    '''
     Encoding of informations related to an Opus, stored in ElasrticSearch
    '''
    corpus_ref = Text()
    id = Integer()
    ref = Text()
    title = Text()
    lyricist = Text()
    composer = Text()
    # Music summary: compressed representation of the music content
    summary = Text()
    #: Ngram encoding of the melody
    melody = Nested(
        doc_class=DescriptorIndex,
    )
    #: Ngram encoding of the rythm
    rhythm = Nested(
        doc_class=DescriptorIndex,
    )
    #: Ngram encoding of the notes
    notes = Nested(
        doc_class=DescriptorIndex,
    )
    #: Text encoding of the lyrics
    lyrics = Nested(
        doc_class=DescriptorIndex,
    )
    # Ngram encoding of the diatonic intervals
    diatonic = Nested(
        doc_class=DescriptorIndex,
    )
    '''
      Add a new descriptor to the OpusIndex. Must be done before sending the latter to ES
    '''
    def add_descriptor(self, descriptor):
        if descriptor.type == settings.LYRICS_DESCR:
            self.lyrics = self.update_list(self.lyrics, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.MELODY_DESCR:
            self.melody = self.update_list(self.melody, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.RHYTHM_DESCR:
            self.rhythm = self.update_list(self.rhythm, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.NOTES_DESCR:
            self.notes = self.update_list(self.notes, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.DIATONIC_DESCR:
            self.diatonic = self.update_list(self.diatonic, descriptor.to_dict(), 'voice')
