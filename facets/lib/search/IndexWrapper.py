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
from lib.search.Sequence import Sequence

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class IndexWrapper:
    """
    
    A class to send queries to ElasticSearch
    
    This class acts as a proxy for all queries sent to ElasticSearch. It relies on
    the ``elasticsearch_dsl`` package, documented here:
    https://elasticsearch-dsl.readthedocs.io/en/latest/. 
    
    """

    def __init__(self, auth_login=None, auth_password=None) :
        """
           Connect to the ElasticSearch server, and open the index
        """
        if auth_login is None:
            self.elastic_search = Elasticsearch(host="localhost", 
                                            port=9200,
                                            index="index")
        else:
            self.elastic_search = Elasticsearch(host="localhost", 
                                            port=9200,
                                            index="index",
                                            http_auth=(auth_login, auth_password))

        # Open, and possibly create the index
        self.index = Index ("index", using=self.elastic_search)
        
        if not self.index.exists(using=self.elastic_search):
            # Create the index
            self.index.create(using=self.elastic_search)
            self.index.settings(number_of_shards=1, number_of_replicas=0)

        self.index.open(using=self.elastic_search)
        #: Directory containing some pre-defined queries in JSON
        self.query_dir = settings.ES_QUERY_DIR
        #ES_QUERY_DIR = os.path.join(BASE_DIR, "static/queries")
    
    def get_index_info(self):
        '''
        Obtain main infos on the index
        '''
        return self.index.get()

    def index_musicdoc(self, MusicDoc, descr_dict):
        """ 
        Add or replace an Opus in the ElasticSearch index
        
        """
        
        print ("Index MusicDoc " + MusicDoc.doc_id)
        # First time that we index this Opus
        try:

            musicdoc_index = MusicDocIndex(
                meta={'id': MusicDoc.doc_id, 'index': "index"}
            )
            
            # Add features/descriptors to index

            """
            for descriptor in descr_dict:
                #print ("Add descriptor for voice " + descriptor.voice, " type " + descriptor.descr_type)
                musicdoc_index.add_descriptor(descriptor)
            """
            #Every voice from the descriptor dict of this musicdoc
            for voice in descr_dict:
                musicdoc_index.add_descriptor(descr_dict[voice])
            
            musicdoc_index.save(using=self.elastic_search, id=MusicDoc.doc_id)

        except Exception as ex:
            print ("Error met when trying to index: " + str(ex))
        
        return

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

class MusicDocIndex(Document):
    '''
     Encoding of informations related to a MusicDoc, stored in ElasticSearch
    '''
    id = Text()
    index = Text()

    #title = Text()
    #composer = Text()
    # Music summary: compressed representation of the music content
    #summary = Text()
    
    #N-gram encoding of the chromatic intervals
    chromatic = Nested( 
        doc_class=DescriptorIndex,
    )
    """
    #: N-gram encoding of the rhythm
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
    # N-gram encoding of the diatonic intervals
    diatonic = Nested(
        doc_class=DescriptorIndex,
    )
    """
    '''
      Add a new descriptor to the OpusIndex. Must be done before sending the latter to ES
    '''
    def add_descriptor(self, descr_dict):
        self.chromatic = self.update_list(self.chromatic, descr_dict["chromatic"], 'voice')
        """
        if descriptor.type == settings.LYRICS_DESCR:
            self.lyrics = self.update_list(self.lyrics, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.CHROMATIC_DESCR:
            self.chromatic = self.update_list(self.chromatic, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.RHYTHM_DESCR:
            self.rhythm = self.update_list(self.rhythm, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.NOTES_DESCR:
            self.notes = self.update_list(self.notes, descriptor.to_dict(), 'voice')
        elif descriptor.type == settings.DIATONIC_DESCR:
            self.diatonic = self.update_list(self.diatonic, descriptor.to_dict(), 'voice')
        """
