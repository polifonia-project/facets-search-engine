from django.conf import settings

import jsonpickle, json
from operator import itemgetter

# import the logging library
import logging

from lib.search.Sequence import Sequence

# Get an instance of a logger
logger = logging.getLogger(__name__)

class MusicSummary:
    """
        Lightweight representation of a music score. Used for pattern search.
        
        A music summary object gives a barebne representation of a music piece. It consists
        of *parts*, which themselves consist of *voices*. Finally each voice is a *sequence* of *items*.
        
        MS objects could be serialized in JSON. 
        Each MS associated with a MusicDoc, could be used for identify occurrences of pattern searches.
    """

    def __init__(self) :
        self.doc_id = ""
        self.parts = {}
        
    def decode(self, json_string):
        '''
           Decode a MusicSummary from its JSON representation 
        '''
        json_obj = json.loads(json_string)

        if "doc_id" in json_obj.keys():

            self.doc_id = json_obj["doc_id"]
            # Music = set of parts

            for part_id in json_obj["parts"].keys():
                part = json_obj["parts"][part_id]
                self.parts[part_id] = {}
                # Parts = set of voices

                for voice_id in part.keys():
                    voice = part[voice_id]
                    self.parts[part_id][voice_id] = Sequence()
                    # Decode the sequence from the voice
                    self.parts[part_id][voice_id].decode(voice)

    def add_part(self, part_id):
        '''Initializes a part'''
        self.parts[part_id] = {}
        
    def add_voice_to_part(self, part_id, voice_id, voice):
        '''Add a voice to a part'''
        self.parts[part_id][voice_id] = voice.convert_to_sequence()
        
    def encode(self):
        '''
           Encode a music summary in in JSON
        '''
        return jsonpickle.encode(self, unpicklable=False)
   
    def find_positions(self, pattern, search_type, mirror_setting = False):
        """ 
            Find the position of a pattern in the voices
            
            The pattern parameter is a Sequence object
            If 'rhythm' is True, the pattern will be decoded as a rhythm, otherwise, as a melody
            Called by views.py
        """
        occurrences = dict()
        for part_id, part in self.parts.items():
            occurrences[part_id] = dict()
            for voice_id, voice in part.items():
                #Calling find_positions() in Sequence.py
                occurrences[part_id][voice_id] = voice.find_positions(pattern, search_type, mirror_setting)
        return occurrences

    def find_matching_ids(self, pattern, search_type, mirror_setting = False):

        ids = list()
        for part_id, part in self.parts.items():
            for voice_id, voice in part.items():
                #Calling find_positions() in Sequence.py
                occurrences = voice.find_positions(pattern, search_type, mirror_setting)
                for occ in occurrences: 
                    for i in occ:
                        # print ("Item match  " + str(i) + " : " + str(voice.items[i]))
                        ids.append(voice.items[i].id)
        return ids

    def find_sequences(self, pattern, search_type, mirror_setting = False):

        sequences = list()
        for part_id, part in self.parts.items():
            #Iterate over parts in MusicSummary
            for voice_id, voice in part.items():
                '''
                    In every part, iterate over sequences of several voices
                    Note that the "voice" here is not a Voice object, but a "Sequence"
                    If iterating over items within sequence is needed,
                    Use "for item in voice.get_items_from_sequence()"
                '''
                #Calling find_positions() in Sequence.py
                occurrences = voice.find_positions(pattern, search_type, mirror_setting)
                for o in occurrences:
                    s = Sequence()
                    for ir in o:
                        s.add_item(voice.items[ir])
                    sequences.append(s)
        return sequences
