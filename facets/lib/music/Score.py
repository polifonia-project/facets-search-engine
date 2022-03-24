from .Voice import Voice

from music21 import *
import music21 as m21

from django.conf import settings
from .MusicSummary import *


class Score:
    """
        Representation of a score as a hierarchy of su-scores / voices
    """
    
    def __init__(self) :
        # A score is made of components, which can be either voices (final) or other scores
        self.id = ""
        self.components = list()
        self.m21_score = None
        return
    
    def load_from_xml(self, xml_path, format):
        """Get the score representation from a MEI or MusicXML document"""

        try:        
            #If the score is in MEI format, convert it to Music21 stream
            if format == "mei":
                with open (xml_path, "r") as meifile:
                    meiString = meifile.read()
                #print ("MEI file: " + meiString[0:40])
                conv = mei.MeiToM21Converter(meiString)
                self.m21_score = conv.run()
            else:
                #If the score is in XML format
                self.m21_score = m21.converter.parseFile(xml_path,format=format)
        
            self.load_component(self.m21_score)

        except Exception as ex:
            self.m21_score = None
            print ("Error while loading from xml:" + str(ex))
            print ("Some error raised while attempting to transform MEI to XML.")
                
    def load_component(self, m21stream):
        '''Load the components from a M21 stream'''

        default_voice_id = 1
        default_part_id = 1
        
        if m21stream == None:
            print("Error while loading from score, the m21 stream is empty.")
            return

        # Extract the voices
        if m21stream.hasVoices():
            for m21voice in m21stream.voices:
                voice = Voice(self.id + "-" + str(default_voice_id))
                voice.set_from_m21(m21voice)
                #print ("Create voice in component " + self.id + " with id " + voice.id)
                default_voice_id += 1
                self.components.append(voice)

        # Extract the parts as sub-scores
        if m21stream.hasPartLikeStreams():
            partStream = m21stream.parts.stream()
            for p in partStream:
                score = Score()
                score.id = "P" + str(default_part_id)
                #print ("Create component score with id " + score.id)
                default_part_id += 1
                self.components.append(score)
                # Recursive call
                score.load_component(p)
                
        # Last case: no voice, no part: the stream itself is a voice
        if not m21stream.hasVoices() and not m21stream.hasPartLikeStreams():
            voice = Voice(self.id + "-" + str(default_voice_id))

            m21voice = m21.stream.Voice(m21stream.flat.notesAndRests.elements)
            # print ("Create voice in component " + self.id + " with id " + voice.id)
            voice.set_from_m21(m21voice)
            voice.convert_to_sequence()

            self.components.append(voice)
        
    def get_sub_scores(self):
        '''Return the score components'''
        scores = list()
        for comp in self.components:
            if isinstance(comp, Score):
                scores.append(comp)
        return scores

    def get_voices(self):
        '''Return the local voices components'''
        voices = list()
        for comp in self.components:
            if isinstance(comp, Voice):
                voices.append(comp)
        return voices
    
    def get_all_voices(self):
        '''Recursive search of all the voices in the score'''
        voices = list()
        for comp in self.components:
            if isinstance(comp, Voice):
                # Add the local voices
                voices.append(comp)
            elif isinstance(comp, Score):
                # Add the voices of the sub-components
                voices += comp.get_all_voices()
        return voices
    
    def get_music_summary(self):
        '''Produce a compact representation of a score for search operations'''

        music_summary = MusicSummary()

        # Adds a single part, for historical reasons: we do not care about parts
        # for search operations
        part_id = settings.ALL_PARTS
        music_summary.add_part(part_id)

        # Now add all the voices
        voices = self.get_all_voices()

        for voice in voices:
            music_summary.add_voice_to_part(part_id, voice.id, voice)

        return music_summary
    
    def get_title(self):
        if self.m21_score.metadata:
            return self.m21_score.metadata.title
        else:
            return ""

    def get_composer(self):
        if self.m21_score.metadata:
            return self.m21_score.metadata.composer
        else:
            return ""
            
    def get_metadata(self):
        return self.m21_score.metadata

    def get_intervals(self):
        return score.chordify()
