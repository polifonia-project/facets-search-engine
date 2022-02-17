# coding: utf-8
from django.conf import settings
from music import *
from .Sequence import Sequence

class SearchContext:
    """
       Representation of a search context
       
       Searching in Neuma involves three components:
          
          - the corpus that defines the search scope
          - a pattern the defines the melodic and / or rhythmic features 
          - keywords, used for meta data and lyrics
          
        The search context is preserved during navigation from one corpus to the
        other, or even from a corpus to some specific opus. It acts as a filter
        which is applied to the corpuses met as the user navigates. It can be cleared
        partially, or totally. In the latter case, no filter is applied to
        the corpus content. It can also be updated as the user defines / changes
        the compoents in the search form.
    """
    def __init__(self) :
        #: The context is either a corpus or an opus
        self.type = settings.CORPUS_TYPE
        #: Default context: the 'all' corpus
        self.ref = settings.NEUMA_ROOT_CORPUS_REF
        #: The melodic pattern
        self.pattern = ""
        #: The set of keywords
        self.keywords = ""
        #: Type of pattern search
        self.rhythmic_search = False
        #: Default type of search
        self.search_type = settings.MELODIC_SEARCH
        #: A variable that holds messages return by a search. 
        self.info_message = ""
        # Mirror search enabled or not
        self.mirror_search = False
        
    def is_opus(self):
        if self.type == settings.OPUS_TYPE:
            return True
        else:
            return False

    def is_corpus(self):
        return not self.is_opus()
    
    def is_keyword_search(self):
        return self.keywords != ""

    def is_pattern_search(self):
        return self.pattern
        
    def is_mirror_search(self):
        return self.mirror_search

    def in_search_mode(self):
        """
           We are in search mode if either keywords or pattern is defined
         """
        return self.keywords != "" or self.pattern != ""

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
            intervals = pattern_seq.get_intervals(settings.MELODY_DESCR)
            if len(intervals) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_melody_encoding(mirror_setting)
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
