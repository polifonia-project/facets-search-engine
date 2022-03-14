import jsonpickle
import string
from fractions import Fraction

#from .Distance import *
#from .Distance_neuma import *

from .Item import Item

from django.conf import settings

import music21 as m21

INTERVAL_SEPARATOR = "|"
DURATION_UNIT = 16


class Sequence:
    """
        A compact representation of a voice, used for search operations
    """
    def __init__(self):
        # A sequence is a list of music items
        self.items = []
        return
        
    def decode(self, json_obj):
        """
        Decode from a JSON object
        """
        for json_item in json_obj["items"]:
            item = Item()
            item.decode(json_item)
            self.add_item(item)

    def encode(self):
        '''Encode in JSON'''
        return jsonpickle.encode(self, unpicklable=False)
 
    def add_item(self, item):
        self.items.append(item)
    
    def get_items_from_sequence(self):
        return self.items

    """
        The functions below are for extracting list of different types of intervals.

            def get_intervals() for chromatic / diatonic intervals,
            def get_rhythms() for rhythmic intervals,
            def get_notes() for both chromatic and rhythmic intervals
            def get_mirror_intervals() for mirroring a list of chromatic / diatonic intervals.

    """

    def get_intervals(self, descriptor="chromatic"):
        """

            Get a list of chromatic or diatonic intervals.
            Default setting: getting the chromatic intervals.

            Ignore repeated notes, grace notes, when there is a rest note,
            made sure it is noticeable in the list of intervals.

            Intervals are encoded as a list of objects (dict). 
            Each object contains the position of the first event, 
            the position of the last event, and the interval value.
            Positions are saved for locating to highlight.

            The list "diatonic_intervals" stores diatonic intervals as value,
            while the list "chromatic_intervals" stores the number of semitones as value.

        """
        dict_wordtonum = {"Unison": '2', "Second": '2', "Third": '3', "Fourth": '4', "Fifth": '5', "Sixth": '6', "Seventh": '7'}
        #P.S.: Unison as "2" instead of "0" for a reason, see explanation later
        
        chromatic_intervals = []
        diatonic_intervals = []
        
        previous_item = None
        i_pos = 0
        current_pos = i_pos
        
        # Scan the items        
        for item in self.items:
            # We ignore rests
            if item.is_rest: 
                # If the rest is a full measure, part of a multi-measure rest: we need to adjust
                i_pos += 1
                continue

            if previous_item is None:
                previous_item = item
            else:
                # gap = number of semi-tones of the current interval 
                gap = item.get_index() - previous_item.get_index()

                if gap != 0:
                    #if a pitch change is detected
                    if gap > 0:
                        #  if the semi-tone difference between the current and the previous item > 0, it is an ascending interval.
                        direction = 'A'
                    else:
                        #  otherwise, it is a descending interval.
                        direction = 'D'

                    if descriptor == "diatonic":
                        """
                        Get diatonic interval name via music21, and store as a dictionary. 
                        Each object contains the position of the first event, the position of the last event,
                        and diatonic interval name. The interval is reduced to no more than an octave.

                        PS:
                        For obtaining original interval name(not reduced to an octave), may change "directedsimpleNiceName" to "niceName".
                        For not getting the direction info(descending or ascending), may change "directedSimpleNiceName" to "simpleNiceName".
                        """

                        #Transfer items to music21 note objects
                        m21_item = item.get_music21_note()
                        m21_pre_item = previous_item.get_music21_note()

                        # Get intervals using music21
                        """
                            "directedSimpleNiceName" examples: "Descending Doubly-Diminished Fifth", "Ascending Perfect Fourth", "Ascending Doubly-Augmented Fourth"
                            "simpleName" examples: dd5, P5, AA4. There's no direction information
                            Since it only executes when a pitch interval is detected, "unison" refers to an augmented unison, a.k.a minor second
                        """
                        m21_interval_directed = m21.interval.Interval(noteStart=m21_pre_item, noteEnd=m21_item).directedSimpleNiceName
                        
                        arr_diatonic = m21_interval_directed.split(" ")

                        m21_generic = dict_wordtonum[arr_diatonic[-1]]

                        m21_interval = m21_generic + direction

                        dia_interval = {"start_pos": current_pos, "end_pos": i_pos, "value": m21_interval}
                        diatonic_intervals.append(dia_interval)

                    # To get the current chromatic interval(represented as semitone numbers)
                    num_interval = str(abs(gap)) + direction
                    chromatic_interval = {"start_pos": current_pos, "end_pos": i_pos, "value": num_interval}
                    chromatic_intervals.append(chromatic_interval)

                    previous_item = item
                    current_pos = i_pos

            i_pos += 1

        if descriptor == "diatonic":
            #return diatonic interval names.
            return diatonic_intervals
        else:
            #return chromatic intervals, which are represented as number of semitones.
            return chromatic_intervals

    def get_rhythms(self):
        '''
            Get the list of rhythms.
            Rhythms are encoded as a list of objects (dict). 
            Each object contains the pos of the first event, the pos of the last event,
            and the interval value.
        '''
        rhythms = []
        previous_item = None

        i_pos = 0
        current_pos = i_pos

        for item in self.items:
                        
            if previous_item is None:
                previous_item = item
            else:
                # Prevent division by zero
                if item.duration == 0 or previous_item.duration == 0:
                    continue
                if item.get_index() == previous_item.get_index():
                    pitch_change = False
                else:
                    pitch_change = True

                #  gap = the ratio between the current note length and the previous one.

                gap = Fraction(Fraction.from_float(item.duration), Fraction.from_float(previous_item.duration)).limit_denominator(max_denominator=10000)

                rhythm = {"start_pos": str(current_pos), "end_pos": str(i_pos), 
                          "value": str(gap), "pitch_change": pitch_change}

                if item.is_rest != True:
                    rhythms.append(rhythm)
                else:
                    #  When there is a rest note
                    #  Set value as -1, to make sure it disrupts a consecutive "rhythm pattern".
                    rhythm = {"start_pos": str(current_pos), "end_pos": str(i_pos), 
                          "value": str(-1), "pitch_change": pitch_change}
                    rhythms.append(rhythm)

                previous_item = item
                current_pos = i_pos
            i_pos += 1

        return rhythms

    def get_notes(self):
        """
            Get notes for exact search.
            Save both rhythm and chromatic intervals.
        """
        notes = []
        previous_item = None
        # Scan the items
        i_pos = 0
        current_pos = i_pos
        for item in self.items:
            if previous_item is None:
                previous_item = item
            else:
                # Prevent division by zero
                item_duration = Fraction.from_float(item.duration).limit_denominator(max_denominator=100)
                previous_item_duration = Fraction.from_float(previous_item.duration).limit_denominator(max_denominator=100)
                if item_duration == 0 or previous_item_duration == 0:
                    continue
                rhythm = Fraction(item_duration, previous_item_duration).limit_denominator(max_denominator=100)
                pitch_temp = item.get_index() - previous_item.get_index()
                if pitch_temp > 0:
                    pitch = str(pitch_temp)+'A'
                else:
                    pitch = str(abs(pitch_temp))+'D'
                note = {"start_pos": str(current_pos), "end_pos": str(i_pos), "rhythm": str(rhythm), "pitch": str(pitch)}
                notes.append(note)
                previous_item = item
                current_pos = i_pos
            i_pos += 1
        return notes

    def get_mirror_intervals(self, intervals):
        """
            Get an interval list(diatonic or melodic), 
            then return the "mirror" of the pattern list.

            It goes through the original interval list,
            and change directions of each interval to the opposite.

            Example: the original representation of an ascending second is "2A", and the mirror representation
            of "2A" is "2D", a.k.a. a descending second.
        """
        
        mirror_intervals = []

        for i in intervals:
            #Iterate over the list of the original intervals
            curr_start_pos = i["start_pos"]
            curr_end_pos = i["end_pos"]
            curr_value = i["value"]
            
            mirror_dir = ''
            if curr_value[-1] == 'A':
                mirror_dir = 'D'
            elif curr_value[-1] == 'D':
                mirror_dir = 'A'

            #Change the direction to its opposite
            mirror_value = curr_value[:-1] + mirror_dir

            mirror_interval = {"start_pos": curr_start_pos, "end_pos": curr_end_pos, "value": mirror_value}
            mirror_intervals.append(mirror_interval)

        return mirror_intervals



    """
        The functions below are for encoding a list of intervals.

            def get_chromatic_encoding() for encoding a list of chromatic intervals.
            def get_diatonic_encoding() for encoding a list of diatonic intervals.
            def get_rhythm_encoding() for encoding a list of rhythmic intervals.
    """


    def get_chromatic_encoding(self, mirror_setting = False, NGRAM_SIZE = 3):
        """
            Get chromatic intervals and decompose in ngram text for chromatic search.
            
            When mirror_setting=True, the search is specified to include mirror patterns in the search context,
            it returns the original chromatic encodings, and the mirrored chromatic encodings, both as a list of n-grams.

            Please find definition of "mirror patterns" in description of def get_mirror_intervals()

        """
        chromatic_list = self.get_intervals("chromatic")
        chromatic_encoding = self.intervals_to_ngrams(chromatic_list, NGRAM_SIZE)

        if mirror_setting == False:
            return chromatic_encoding
        elif mirror_setting == True:
            mirror_chromatic = self.get_mirror_intervals(chromatic_list)
            return chromatic_encoding, self.intervals_to_ngrams(mirror_chromatic)


    def get_diatonic_encoding(self, mirror_setting = False, NGRAM_SIZE = 3):
        """
            Get diatonic interval names and decompose in ngram text for diatonic search.

            When mirror_setting=True, it means that the search specified to include mirror patterns in the search context,
            this function returns the original diatonic encodings, and the mirrored diatonic encodings, both as a list of n-grams.

        """
        dia_list = self.get_intervals("diatonic")
        dia_encoding = self.intervals_to_ngrams(dia_list, NGRAM_SIZE)

        if mirror_setting == False:
            return dia_encoding
        elif mirror_setting == True:
            mirror_dia = self.get_mirror_intervals(dia_list)
            return dia_encoding, self.intervals_to_ngrams(mirror_dia)

    def intervals_to_ngrams(self, dict, NGRAM_SIZE = 3):
        """
            Splits intervals into ngrams with size NGRAM_SIZE, for melodic / diatonic search.
        """
        nb_codes = len(dict)
        phrase = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            #ngram no longer needs to begin with a separator ';' because it's absolute value
            ngram = ""
            for j in range(i, i + NGRAM_SIZE): 
                ngram = ngram + str(dict[j]["value"]) + ";"
            phrase += ngram + " N "
        return phrase

    """
        Encoding rhythm intervals
    """

    def get_rhythm_encoding(self, NGRAM_SIZE = 3):
        """
            Get rhythm and decompose in ngram text for rhythmic search
        """
        rhythm_encoding = self.rhythms_to_ngrams(self.get_rhythms(), NGRAM_SIZE)
        return rhythm_encoding

    def rhythms_to_ngrams(self, dict, NGRAM_SIZE = 3):
        #
        #   Splits rhythms ratios into ngrams with size NGRAM_SIZE, e.g : (3/4)(2/3)(1/2) (2/3)(1/2)(1/2) ...
        #
        nb_codes = len(dict)
        text = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            ngram = ""
            for j in range(i, i + NGRAM_SIZE):
                # Surround ratios with parentheses
                ngram += "(" + str(dict[j]["value"]) + ")"
            text += ngram + " N "
        return text


    """
        Encoding notes
    """
    def get_note_encoding(self, NGRAM_SIZE = 3):
        """
            Get note and decompose in ngram text for exact search
        """
        note_encoding = self.to_ngrams(self.notes_to_symbols(self.get_notes()), NGRAM_SIZE)
        return note_encoding

    @staticmethod
    def notes_to_symbols(dict):
        symbols = list()
        for note in dict:
            symbols.append('(' + str(note['pitch']) + '|' + str(note['rhythm']) + ')')
        return symbols

    def to_ngrams(self, symbols, hash=False, NGRAM_SIZE = 3):
        #
        #   Splits symbol list into ngrams with size NGRAM_SIZE, used for exact search
        #
        nb_codes = len(symbols)
        phrase = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            ngram = ""
            for j in range(i, i + NGRAM_SIZE):
                ngram = ngram + str(symbols[j]) + ""
            #if hash:
            #    phrase += self.hash_ngrams(ngram) + " "
            else:
                phrase += ngram + " N "
        return phrase

    @staticmethod
    def find_sub_list(sub_list, l):
        # Find sublists in list
        # Returns a list of the first and last indexes of the matching sublists
        results = []
        sll = len(sub_list)
        for ind in (i for i, e in enumerate(l) if e == sub_list[0]):
            if l[ind:ind + sll] == sub_list:
                results.append((ind, ind + sll - 1))
        return results

    def __str__(self):
        s = ""
        sep = ""
        for item in self.items:
            s =  s + sep + str(item) 
            sep = ";"
        return s

    """
    find positions
    """

    @staticmethod
    def get_intervals_as_list(intervals):
        """
            Get intervals value in a list
        """
        interval_list = []
        for interval in intervals:
            interval_list.append(str(interval["value"]))
        return interval_list

    def find_positions(self, pattern, search_type, mirror_setting = False):
        """
         Find the position(s) of a pattern in the sequence
         p_intervals: the encoded pattern to search for
         s_intervals: all the intervals/sequences from each voice
         m_intervals: mirror pattern of the original pattern
         the goal is to find p_intervals_list in s_intervals_list
        """
        occurrences = []

        if search_type == settings.RHYTHMIC_SEARCH:
            p_intervals = pattern.get_rhythms()
            s_intervals = self.get_rhythms()
            m_intervals = ""

        elif search_type == settings.CHROMATIC_SEARCH:
            p_intervals = pattern.get_intervals(settings.CHROMATIC_DESCR)
            m_intervals = pattern.get_mirror_intervals(p_intervals)
            s_intervals = self.get_intervals(settings.CHROMATIC_DESCR)

        elif search_type == settings.EXACT_SEARCH:
            p_intervals = pattern.get_notes()
            s_intervals = self.get_notes()

        elif search_type == settings.DIATONIC_SEARCH:
            p_intervals = pattern.get_intervals(settings.DIATONIC_DESCR)
            m_intervals = pattern.get_mirror_intervals(p_intervals)
            s_intervals = self.get_intervals(settings.DIATONIC_DESCR)
        else:
            #if search type is not defined, default setting is melody search
            p_intervals = pattern.get_intervals(settings.CHROMATIC_DESCR)
            s_intervals = self.get_intervals(settings.CHROMATIC_DESCR)

        # Get intervals as list, e.g. ['2', '2', '2']
        if search_type == settings.EXACT_SEARCH:
            p_intervals_list = self.notes_to_symbols(p_intervals)
            s_intervals_list = self.notes_to_symbols(s_intervals)
        else:
            p_intervals_list = pattern.get_intervals_as_list(p_intervals)
            m_intervals_list = pattern.get_intervals_as_list(m_intervals)
            s_intervals_list = pattern.get_intervals_as_list(s_intervals)
        
        # Find patterns positions in list
        occurrences_indexes = self.find_sub_list(p_intervals_list, s_intervals_list)

        #If it is mirror search, the function also finds the positions of mirror patterns
        if mirror_setting == True:
            mirror_occ_indexes = self.find_sub_list(m_intervals_list, s_intervals_list)

            #Add mirror pattern occurrences into occurrences_indexes
            for occ in mirror_occ_indexes:
                occurrences_indexes.append(occ)
        
        for tuple in occurrences_indexes:
            # Get start and end positions
            occurrences.append(range(int(s_intervals[tuple[0]]["start_pos"]), int(s_intervals[tuple[1]]["end_pos"]) + 1))

        return occurrences
