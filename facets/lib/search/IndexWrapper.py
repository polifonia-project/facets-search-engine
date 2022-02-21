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

        #: Directory containing some pre-defined queries in JSON
        #self.query_dir = settings.ES_QUERY_DIR
    
    def index_exists(self, index_name):
        #Check if the index exists in ES and return
        return

    def get_index_info(self):
        '''
        Obtain main infos on the index
        '''
        return self.index.get()

    def index_musicdoc(self, index_name, MusicDoc, descr_dict):
        """ 
        Add or replace a MusicDoc in the ElasticSearch index
        
        """
        
        print ("Index MusicDoc " + MusicDoc.doc_id)

        try:

            musicdoc_index = MusicDocIndex(
                meta={'id': MusicDoc.doc_id, 'index': index_name}
            )

            """
            # Iterate over types of descriptors in the dictionary
            # For example, descr_dict["chromatic"]["P1-1"]["value"] contains the chromatic descriptor of voice P1-1 of the doc
            for descr_type in descr_dict:
                #Iterate over parts in one type of descriptor
                for part in descr_dict[descr_type]:
                    part_id = descr_dict[descr_type][part]["part"]
                    voice_id = descr_dict[descr_type][part]["voice"]
                    des_value = descr_dict[descr_type][part]["value"]

            """

            # Add/update descriptors(a.k.a. features) to ES index
            musicdoc_index.add_descriptor(descr_dict)
            # Save the updated index
            musicdoc_index.save(using=self.elastic_search, id=MusicDoc.doc_id)

        except Exception as ex:
            print ("Error met when trying to index: " + str(ex))
        
        return

class DescriptorIndex(InnerDoc):
    '''
     Encoding of a specific descriptor for a voice, stored in ElasticSearch
     
     A descriptor is a character string that encodes a specific aspect (rhythm, melody, lyrics)
     of a voice in a music piece. Its structure (sequence of n-grams) is such that effective text-based search
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

        # To be modified: voices are there as a highest hierachy
        self.chromatic = descr_dict["chromatic"]
        self.diatonic = descr_dict["diatonic"]
        self.rhythm = descr_dict["rhythmic"]
        self.notes = descr_dict["notes"]
        #self.lyrics = descr_dict["lyrics"]
