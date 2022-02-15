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

