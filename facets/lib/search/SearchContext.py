# coding: utf-8
from django.conf import settings
from music import *
from .Sequence import Sequence
from music21 import *

class SearchContext:
    """
       Representation of a search context
          
          - a search type that defines the type of search content
          - pattern context that you wish to search for 
          - text context, for searching within lyrics and metadata information
          - mirror search, could be enabled for chromatic, diatonic and rhythmic search. 
          
    """
    def __init__(self) :        
        self.search_type = settings.CHROMATIC_SEARCH
        self.pattern_context = ""
        self.text_context = ""
        # Mirror search enabled or not
        self.mirror_search = False
        
    def is_text_search(self):
        return self.text_context != ""
        
    def is_mirror_search(self):
        return self.mirror_search

    def in_search_mode(self):
        """
           We are in search mode if either keywords or pattern is defined
         """
        #TO-DO: add the code to validate if pattern is valid, 
        #using check_pattern_length
        return self.text_context != "" or self.pattern_context != ""

    def decode_pattern_context(self):
        # self.pattern_context is abc format
        # Transform abc into music21 object
        m21_pattern = converter.parse(self.pattern_context)

        # Transform music21 into Items
        item_list = []
        
        # To be checked: iterate over m21 pattern
        for m21_note in m21_pattern:
            newitem = Item()
            newitem.m21_to_item(m21_note)
            item_list.append(newitem)
        
        return item_list

    def get_pattern_sequence(self):
        ''' Decode the pattern as a Sequence object '''
        pattern_seq = Sequence()
        if self.pattern:
            pattern_seq = Sequence()
            pattern_seq.set_from_pattern(self.pattern)
        return pattern_seq

    def check_pattern_length(self):
        '''
          Check if length of pattern is larger than ngram size
        '''
        if self.pattern != "":
            pattern_seq = self.get_pattern_sequence()
            pattern_len = len(pattern_seq.items)
            if pattern_len <= settings.NGRAM_SIZE:
                return False
            return True
        else:
            return False

    def get_melodic_pattern(self, mirror_setting=False):
        '''
          Transform the melodic pattern to an ngram representation
        '''
        
        if self.pattern != "":
            pattern_seq = self.get_pattern_sequence()
            # Check that the number of intervals is at least an ngram size
            intervals = pattern_seq.get_intervals(settings.CHROMATIC_DESCR)
            if len(intervals) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_chromatic_encoding(mirror_setting)
        else:
            return ""

    def get_rhythmic_pattern(self):
        '''
         Transform the rhythmic pattern to an ngram representation
         '''
        if self.pattern != "":
            pattern_seq = self.get_pattern_sequence()
            # Check that the number of intervals is at least an ngram size
            rhythms = pattern_seq.get_rhythms()
            if len(rhythms) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_rhythm_encoding()
        else:
            return ""

    def get_diatonic_pattern(self, mirror_setting=False):
        '''
            Transform diatonic intervals to n-gram representation
        '''

        if self.pattern != "":
            pattern_seq = self.get_pattern_sequence()
            # Check that the number of intervals is at least an ngram size
            diatonic_inter = pattern_seq.get_intervals(settings.DIATONIC_DESCR)
            if len(diatonic_inter) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_diatonic_encoding(mirror_setting)
        else:
            return ""

    def get_notes_pattern(self):
        '''
           Obtain the sequence of notes from the pattern
          '''
        if self.pattern != "":
            pattern_seq = self.get_pattern_sequence()
            return pattern_seq.get_note_encoding()
        else:
            return ""
