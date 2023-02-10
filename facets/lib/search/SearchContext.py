# coding: utf-8
from django.conf import settings
from lib.music.Score import *
from lib.music.Voice  import *
from .Sequence import Sequence
from music21 import *
import re

class SearchContext:
    """
       Representation of a search context
          
          - a search type that defines the type of search content
          - pattern that you wish to search for 
          - text, for searching within lyrics and metadata information
          - mirror search, could be enabled for chromatic, diatonic and rhythmic search. 
          
    """
    def __init__(self) :
        self.index = ""
        # TODO: FOR NOW facet_composers and facet_instruments are strings, when there're multiple selections we change to []
        self.facet_composers = "" 
        self.facet_instruments = ""
        self.facet_keymode = ""
        self.facet_keytonicname = ""
        self.search_type = settings.CHROMATIC_SEARCH
        self.pattern = ""
        self.pianopattern = ""
        self.text = ""
        # Mirror search enabled or not
        self.mirror_search = False
    
    def where_to_search(self):
        return self.index

    def is_text_search(self):
        return self.text != ""
        
    def facet_composer(self):
        return self.facet_composers

    def is_pattern_search(self):
        return self.pattern != "" or self.pianopattern != ""

    def is_mirror_search(self):
        return self.mirror_search

    def in_search_mode(self):
        """
           We are in search mode if either keywords or pattern is defined
         """
        #TO-DO: add the code to validate if pattern is valid, 
        #using check_pattern_length
        return self.text != "" or self.pattern != "" or self.pianopattern != ""

    def read(self, search_input):

        # Read from the input and make a SearchContext out of it
        self.index = search_input["index_name"]
        self.search_type = search_input["type"]
        if "pianopattern" in search_input:
            self.pianopattern = search_input["pianopattern"]
            # decode, get a sequence of items
            #self.decode_piano_pattern()
        if "pattern" in search_input:
            # Only if there is no input from piano. Otherwise we discard ABC pattern to avoid confusion
            if not self.pianopattern:
                self.pattern = search_input["pattern"]
        if "text" in search_input:
            self.text = search_input["text"]
        if "mirror" in search_input:
            if search_input["mirror"] == "True":
                self.mirror_search = True
            else:
                self.mirror_search = False
        if "composer" in search_input:
            # This should be a list of composer names from the search input
            # TODO: when searchinput can be multiple selection, it needs to change from string to list
            #if type(search_input["composer"]) != list:
            if search_input["composer"] != "Composers" and search_input["composer"] != "Composer":
                # if no composer is selected, it should be Composers
                self.facet_composers = search_input["composer"]

        if "instrument" in search_input:
            if search_input["instrument"] != "instruments" and search_input["instrument"] != "Instruments":
                self.facet_instruments = search_input["instrument"]
        if "keymode" in search_input:
            if search_input["keymode"] != "Key mode" and search_input["keymode"] != "key mode":
                self.facet_keymode = search_input["keymode"]
        if "keytonicname" in search_input:
            if search_input["keytonicname"] != "Key tonic name" and search_input["keytonicname"] != "key tonic name":
                self.facet_keytonicname = search_input["keytonicname"]
        #if "numofparts" in search_input
        # Other facets to be continued..
        

    def check_default_meter(self):
        # For ABC pattern:
        # Check if the pattern contains definition of meter or unit note length
        # If not, add 1/4 as unit note length
        
        abcStr = self.pattern
        indexes = [x.start() for x in re.finditer(':', abcStr)]
        
        # Check if meter or unit note length is defined
        meterexists = False
        for i in indexes:
            if abcStr[i-1] == 'M' or abcStr[i-1] == 'L':
                meterexists = True

        # Set unit note length as 1/4 if not defined
        if meterexists == False:
            abcStr = "L:1/4\n" + abcStr
            # if you wish to set 4/4 as meter
            # instead of using quarter note as unit note length:
            #abcStr = "M:4/4\n" + abcStr

        return abcStr

    def decode_piano_pattern(self):
        # Call Sequence.py to decode piano pattern to normal pattern
        pattern_seq = Sequence()
        if self.pianopattern:
            item_list = pattern_seq.set_from_pianopattern(self.pianopattern)
        return item_list

    def decode_pattern_context(self):
        # This function process abc format patterns -> a m21 stream -> a list of Items.

        # assume self.pattern is abc format
        
        abcStr = self.pattern
        # Make sure there is a meter or unit note length
        abcStr = self.check_default_meter()
        handler = abcFormat.ABCHandler()
        handler.process(abcStr)
        m21score = m21.abcFormat.translate.abcToStreamScore(handler)

        # Transform music21 notes into Items
        item_list = []
        for m21_note in m21score.recurse().notes:
            newitem = Item()
            newitem.m21_to_item(m21_note)
            item_list.append(newitem)
        return item_list

    def get_pattern_sequence(self):
        ''' Given the pattern content, output a Sequence obj representing the pattern'''
        pattern_seq = Sequence()
        if self.pianopattern:
            pattern_seq.set_from_pianopattern(self.pianopattern)
        elif self.pattern:
            list_of_items = self.decode_pattern_context()
            for item in list_of_items:
                pattern_seq.add_item(item)

        return pattern_seq

    def check_pattern_length(self):
        '''
          Check if length of pattern is larger than ngram size
        '''
        if self.pattern != "" or self.pianopattern != "":
            pattern_seq = self.get_pattern_sequence()
            pattern_len = len(pattern_seq.items)
            if pattern_len <= settings.NGRAM_SIZE:
                return False
            return True
        else:
            return False

    def get_chromatic_pattern(self, mirror_setting=False):
        '''
          Transform the melodic pattern to an ngram representation
        '''
        
        if self.pattern != "" or self.pianopattern != "":
            pattern_seq = self.get_pattern_sequence()
            # Check that the number of intervals is at least an ngram size
            intervals = pattern_seq.get_intervals(settings.CHROMATIC_DESCR)
            if len(intervals) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_chromatic_encoding(mirror_setting)
        else:
            return ""

    def get_diatonic_pattern(self, mirror_setting=False):
        '''
            Transform diatonic intervals to n-gram representation
        '''

        if self.pattern != "" or self.pianopattern != "":
            pattern_seq = self.get_pattern_sequence()
            # Check that the number of intervals is at least an ngram size
            diatonic_inter = pattern_seq.get_intervals(settings.DIATONIC_DESCR)
            if len(diatonic_inter) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_diatonic_encoding(mirror_setting)
        else:
            return ""

    def get_rhythmic_pattern(self):
        '''
         Transform the rhythmic pattern to an ngram representation
         '''
        if self.pattern != "" or self.pianopattern != "":
            pattern_seq = self.get_pattern_sequence()
            # Check that the number of intervals is at least an ngram size
            rhythms = pattern_seq.get_rhythms()
            if len(rhythms) < settings.NGRAM_SIZE:
                return ""
            else:
                return pattern_seq.get_rhythm_encoding()
        else:
            return ""

    def get_notes_pattern(self):
        '''
           Obtain the sequence of notes from the pattern
          '''
        if self.pattern != "" or self.pianopattern != "":
            pattern_seq = self.get_pattern_sequence()
            return pattern_seq.get_note_encoding()
        else:
            return ""
