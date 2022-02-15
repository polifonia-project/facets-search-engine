from .Item import Item
import jsonpickle
import string
from fractions import Fraction
#from .Distance import *
#from .Distance_neuma import *
from django.conf import settings
import music21 as m21

INTERVAL_SEPARATOR = "|"
DURATION_UNIT = 16


class Sequence:
    """
        A compact representation of a voice, used
        for search operations
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

    def set_from_pattern(self, str_pattern):
        """
        Take a string representing the pattern, as supplied by the piano: A4-8;G5-4, etc.
        Create the sequence from this encoding
        """
        if str_pattern == "":
            return ""
        
        # Split the pattern string to identify each note
        split_pattern = str_pattern.split(";")
        
        # Split each note to get the melody and rhythm
        for note in split_pattern:
            decomp_note = note.split("-")
            item = Item()
            # Now, decompose each note
            item.step = decomp_note[0][0]
            if decomp_note[0][1].isdigit():
                item.octave = int(decomp_note[0][1])
                item.alteration = 0
            else:
                if decomp_note[0][1] == 'b':
                    item.alteration = -1
                else:
                    item.alteration = 1
                item.octave = int(decomp_note[0][2])
            item.duration = float(4/float(decomp_note[1][0]))
            self.add_item(item)
        return True

    def get_intervals(self, descriptor="chromatic"):
        """
            Get the list of intervals. Ignore repeated notes, grace notes, 
            and rests / silences.

            Intervals are encoded as a list of objects (dict). Each object 
            contains the pos of the first event, the pos of the last event,
            and the interval value.

            The list "diatonic_intervals" stores diatonic intervals(for example, an ascending fifth is a diatonic interval),
            while the list "intervals" stores the number of semitones as value.
        """
        dict_wordtonum = {"Unison": '2', "Second": '2', "Third": '3', "Fourth": '4', "Fifth": '5', "Sixth": '6', "Seventh": '7'}
        #P.S.: Unison as "2" instead of "0" for a reason, see explanation later
        intervals = []
        diatonic_intervals = []
        previous_item = None
        # Scan the items
        i_pos = 0
        current_pos = i_pos
        for item in self.items:
            # We ignore rests
            if item.is_rest: 
                # If the rest is a full measure, part of a multi-measure rest: we need to adjust
                i_pos += 1
                continue

            if previous_item is None:
                previous_item = item
            else:
                # Compute the number of semi-tones
                gap = item.get_index() - previous_item.get_index()

                if gap != 0:
                    #if we find a new note with different pitch
                    if gap > 0:
                        #if the semi-tone difference between the current and the previous item > 0, then it is an ascending interval
                        direction = 'A'
                    else:
                        #otherwise, it is a descending interval.
                        direction = 'D'

                    if descriptor == settings.DIATONIC_DESCR:
                        """
                        Get diatonic interval name via music21, and store as a dictionary. 
                        Each object contains the position of the first event, the position of the last event,
                        and diatonic interval name. The interval is reduced to no more than an octave.

                        P.S:
                        For obtaining original interval name(not reduced to an octave), may change "directedsimpleNiceName" to "niceName".
                        For not getting the direction info(descending or ascending), may change "directedSimpleNiceName" to "simpleNiceName".
                        """

                        #Transfer items to music21 note objects
                        m21_item = item.get_music21_note()
                        m21_pre_item = previous_item.get_music21_note()

                        #Calculate interval with music21
                        """
                            "directedSimpleNiceName" examples: "Descending Doubly-Diminished Fifth", "Ascending Perfect Fourth", "Ascending Doubly-Augmented Fourth"
                            "simpleName" examples: dd5, P5, AA4. There's no direction information
                            Since the program only executes here when a new note with different pitch is detected, the "unison" here should be an augmented unison, a.k.a minor second
                        """
                        m21_interval_directed = m21.interval.Interval(noteStart=m21_pre_item, noteEnd=m21_item).directedSimpleNiceName
                        
                        arr_diatonic = m21_interval_directed.split(" ")
                        """
                        #This part is no longer necessary because we could tell direction by gap value                            
                        if arr_diatonic[0] == "Ascending": direction = 'A'
                        elif arr_diatonic[0] == "Descending": direction = 'D'
                        else: direction = ''
                        """
                        m21_generic = dict_wordtonum[arr_diatonic[-1]]
                        #m21_generic_interval = m21.interval.GenericInterval(arr_diatonic[-1])

                        m21_interval = m21_generic + direction

                        dia_interval = {"start_pos": current_pos, "end_pos": i_pos, "value": m21_interval}
                        diatonic_intervals.append(dia_interval)


                    # For getting semitone numbers of the current interval
                    num_interval = str(abs(gap)) + direction
                    interval = {"start_pos": current_pos, "end_pos": i_pos, "value": num_interval}
                    intervals.append(interval)

                    previous_item = item
                    current_pos = i_pos

            i_pos += 1

        if descriptor == settings.DIATONIC_DESCR:
            #by diatonic interval names
            return diatonic_intervals
        else:
            #by number of semitones
            return intervals

    @staticmethod
    def get_intervals_as_list(intervals):
        """
            Get intervals value in a list
        """
        interval_list = []
        for interval in intervals:
            interval_list.append(str(interval["value"]))
        return interval_list

    @staticmethod
    def encode_as_string(intervals):
        """
          Encode the intervals as string 
        """
        s_intervals = INTERVAL_SEPARATOR
        for interval in intervals:
            s_intervals = s_intervals + str(interval["value"]) + INTERVAL_SEPARATOR
        return s_intervals
            
    def get_intervals_as_string(self):
        """Used for debugging in templates """
        return self.encode_as_string(self.get_intervals())
    
    def get_melody_encoding(self, mirror_setting = False, NGRAM_SIZE = 3):
        """
            Get melody and decompose in ngram text for melodic search.
            
            When mirror_setting=True, it means that the search specified to include mirror patterns in the search context,
            this function returns the original melody encodings, and the mirrored melody encodings, both as a list of n-grams.

            Please find definition of "mirror patterns" in description of get_mirror_intervals()

        """
        melody_list = self.get_intervals("chromatic")
        melody_encoding = self.intervals_to_ngrams(melody_list, NGRAM_SIZE)

        if mirror_setting == False:
            return melody_encoding
        elif mirror_setting == True:
            mirror_melody = self.get_mirror_intervals(melody_list)
            return melody_encoding, self.intervals_to_ngrams(mirror_melody)

    def intervals_to_ngrams(self, dict, NGRAM_SIZE = 3):
        #
        #   Splits intervals into ngrams with size NGRAM_SIZE, for both melodic and diatonic searches
        #
        nb_codes = len(dict)
        phrase = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            #ngram no longer needs to begin with a separator ';' because it's absolute value
            ngram = ""
            for j in range(i, i + NGRAM_SIZE): 
                ngram = ngram + str(dict[j]["value"]) + ";"
            phrase += ngram + " N "
        return phrase

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

    def sequence_to_symbols(self):
        notes = list()
        for item in self.items:
            s = str(item.get_index()) + '|' + str(Fraction.from_float(item.duration))
            notes.append(s)
        return notes
