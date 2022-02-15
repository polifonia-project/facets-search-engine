import json
import music21 as m21

from pprint import pprint
from collections import namedtuple, OrderedDict
from fractions import Fraction

#import manager.models

from lib.search.Item import Item
from lib.search.Sequence import Sequence

#from home.templatetags.extras import scale_degree, semitoneconv
#from home.templatetags.extras import rhythm_figures_print

DURATION_UNIT = 16


class Voice:
    """
        Representation of a voice in a score. A voice is a sequence of events
        with non-null duration
    """
    
    def __init__(self, id) :
        # A voice has an id, and the sequence is represented as a Music21 stream
        self.id = id
        self.m21_stream = None
        return
    
    def set_from_m21(self, m21stream):
        """Feed the voice representation from a MusicXML document"""
        
        self.m21_stream = m21stream
        
    def get_half_step_intervals(self):
        '''Return half-steps intervals'''
        hs_inter = list()
 
        intervals = self.m21_stream.melodicIntervals()
        for inter in intervals:
            hs_inter.append(int(inter.cents / 100))
            
        return hs_inter
    
    def convert_to_sequence(self):
        sequence = Sequence()
        for event in self.m21_stream.notesAndRests:
            item = Item()
            item.duration = float(event.duration.quarterLength)
            if isinstance(event, m21.note.Note):
                item.id = event.id
                item.step = event.pitch.step
                item.octave = event.pitch.octave
                if event.pitch.accidental is not None:
                    item.alteration = int(event.pitch.accidental.alter)
                else:
                    item.alteration = 0
                if event.lyric != None:
                    item.lyric = event.lyric
                sequence.add_item(item)
            elif isinstance(event, m21.note.Rest):
                item.id = event.id
                item.is_rest = True
                sequence.add_item(item)
            elif isinstance(event, m21.chord.Chord):
                item.id = event.id
                # Get highest pitch in chord
                highest_pitch = event.pitches[-1]
                item.step = highest_pitch.step
                item.octave = highest_pitch.octave
                if highest_pitch.accidental is not None:
                    item.alteration = int(highest_pitch.accidental.alter)
                else:
                    item.alteration = 0
                sequence.add_item(item)
        return sequence
    
    def has_lyrics(self):
        for event in self.m21_stream.notesAndRests:
            if event.lyric != None:
                return True
        return False
    
    def get_lyrics(self):
        if self.has_lyrics():
            return m21.text.assembleLyrics(self.m21_stream).replace('-', '')

    def search_in_lyrics(self, keyword):
        ls = m21.search.lyrics.LyricSearcher(self.m21_stream)
        keyword_results = ls.search(keyword)

        id_list = []
        for result in keyword_results:
            #Within every match of keyword
            #print("measure start, end: ", result.mStart, result.mEnd)

            #Get Music21 Note ID of the note that matched
            #print("note:", result.els[0])
            #print("note measurenumber", result.els[0].measureNumber)
            #print("note offset", result.els[0].offset)
            #print("note duration", result.els[0].duration.quarterLength)
            for item in result.els:
                id_list.append(item.id)

        return len(keyword_results), id_list

    def get_intervals(self):
        ''' Returns the number of occurrences for each interval in Voice '''
        intervals = self.get_half_step_intervals()
        occurrences = {}
        for i in intervals:
            if i in occurrences:
                occurrences[i]+=1
            else:
                occurrences[i] = 1
        return occurrences

    #returns normalized values for intervals FIXME
    def get_intervals_norm(self):
        occurrences = self.get_intervals()
        s = sum(list(occurrences.values()))
        freq = OrderedDict({i:0 for i in range(-12,13)})
        for i in occurrences:
            if i in freq: #prevents adding intervals larger than 1 octava
                freq[i] = float(occurrences[i])/s

        return freq

    def get_ambitus(self):
        i = self.m21_stream.analyze('ambitus')
        return int(i.cents / 100)

    def get_keysignature(self):
        k = self.m21_stream.analyze('key')
        return [k,k.correlationCoefficient,k.alternateInterpretations]

    def get_pitches(self):
        # Valid key adjustment for sorting pitches
        def pitch_to_int(x):
            return (int(x[0][-1])*1000+ord(x[0][0]),x[1])

        all_pitches = OrderedDict({})
        for n in self.m21_stream.notes:

            if isinstance(n,m21.chord.Chord):
                x = str(n.pitches[-1])
            else:
                x = str(n.pitch)

            if x in all_pitches:
               all_pitches[x] += 1
            else:
                all_pitches[x] = 1

        # Note : sorted returns a list, need to reconvert to OrderedDict after
        # sorting
        return OrderedDict(sorted(all_pitches.items(),key=lambda x:pitch_to_int(x)))

    #Normalized version of "get_pitches"
    def get_pitches_norm(self):
        all_freq_pitches = OrderedDict({0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0,11:0})
        ctn = len(self.m21_stream.notes)

        if not ctn:  #just to avoid /0
            ctn = -1

        for n in self.m21_stream.notes:

            if isinstance(n,m21.chord.Chord):
                x = n.pitches[-1].midi%12
            else:
                x = n.pitch.midi%12

            if x in all_freq_pitches:
               all_freq_pitches[x] += 1
            else:
                all_freq_pitches[x] = 1 
        x = {k: float(v)/float(ctn) for k, v in all_freq_pitches.items()}
        return OrderedDict(x)

    def get_pitches_duration(self):
        all_pitches = {}
        for n in self.m21_stream.notes:
            x = str(n.pitch)
            if x in all_pitches:
               all_pitches[x] += float(n.duration.quarterLength) # value / UoM is not important
            else:
                all_pitches[x] = float(n.duration.quarterLength) # only ratio is useflul
        return all_pitches

    def get_midi_pitches(self):
        midi_pitches = {}
        for n in self.m21_stream.notes:
            x = int(n.pitch.midi) % 12
            if x in midi_pitches:
               midi_pitches[x] += 1
            else:
                midi_pitches[x] = 1 
        return midi_pitches

    def get_degrees(self):
        # First, we need to get key signature and tonality
        # From this, we can get the fundamental (which is for example the root 
        # note in the major scale)

        # There is maybe a simpler way to do it ...
        a = self.get_keysignature()[0].getScale('major')

        # Now, we've got the midi pitch of the fundamental (% 12)
        base_pitch   = a.pitches[0].midi % 12

        # Here we have all midi pitches (%12) for the Voice
        midi_pitches = self.get_midi_pitches()

        all_degrees = {}
        for n in self.m21_stream.notes:
            x = (n.pitch.midi - base_pitch + 12)%12
            if x in all_degrees:
                all_degrees[x] += 1
            else:
                all_degrees[x] = 1
        return all_degrees


    def get_degrees_norm(self):
        ctn = len(self.m21_stream.notes)
        x = {k: float(v)/float(ctn) for k, v in self.get_degrees().items()}
        return OrderedDict(x)

    def get_time_signatures(self):

        all_ts = self.m21_stream.getTimeSignatures()
        return all_ts

    def count_measures(self):
        return len(self.m21_stream.getElementsByClass('Measure'))

    def format_rhythmicfigures(self):
        # Philippe: methode annulee car renvoie une erreur "'method' object is not iterable"
        return list()
    
        RhythmFigure = namedtuple('RhythmFigure', ['start', 'duration'])
        def process(tu):
            return RhythmFigure(
                       start=Fraction(tu.offset),
                       duration=Fraction(tu.endTime-tu.offset)
                   )

        a = list(map(process,self.m21_stream.offsetMap))
        return a

    def get_rhythmic_variation(self):
        x = list(map(lambda z:z.start,self.format_rhythmicfigures()))
        return [x[n]-x[n-1] for n in range(1,len(x))] # should work

    def get_onbeat_rhythmicsfigures(self):
        # FIXME : need to add timesignature to this. This one is based on 4/4 only

        all_ts = self.get_timesignatures()

        # FIXME: denominator here should change along with time signature
        #
        # e.g 4/4 > quarter base, 6/8 > eight base.
        onbeat = list(filter(lambda x:(x.start.denominator==1),
                      self.get_rhythmicfigures())
                 )
        return onbeat

    def test_offset_render(self):
        x = self.test_offset()

    def get_rhythms(self):
        all_figs = {}
        r = self.format_rhythmicfigures()
        for f in r:
            if f.duration in all_figs:
                all_figs[f.duration] += 1
            else:
                all_figs[f.duration] = 1
        return all_figs

    def get_rhythmicfigures_norm(self):
        all_figs = {}
        r = self.format_rhythmicfigures()
        ctn = len(self.m21_stream.notes)
        for f in r:
            if f.duration in all_figs:
                all_figs[f.duration] += 1
            else:
                all_figs[f.duration] = 1
        x = {k: float(v)/float(ctn) for k, v in all_figs.items()}
        return OrderedDict(x)

    def list_rhythms(self):
        a = []
        for i in self.format_rhythmicfigures():
            a.append(float(i.duration))
        return a

    def get_pitches_histogram(self):
        pitches = self.get_pitches()
        labels = map(lambda x: "'"+x+"'",pitches.keys())
        #no need for closure here, using music21 _str_
        return manager.models.Histogram(pitches.values(),labels,'Pitches')

    def get_intervals_histogram(self):
        intervals = self.get_intervals()
        return manager.models.Histogram(intervals.values(),intervals.keys(),
            'Intervals',semitoneconv)

    def get_degrees_histogram(self):
        degrees = self.get_degrees()
        return manager.models.Histogram(degrees.values(),degrees.keys(),
            'Degrees',scale_degree)

    def get_rhythms_histogram(self):
        rhythms = self.get_rhythms()
        return manager.models.Histogram(rhythms.values(),rhythms.keys(),
            'Rhythms',rhythm_figures_print)


    def get_histogram(self,measure):
        c = {'pitches':self.get_pitches_histogram,
             'intervals':self.get_intervals_histogram,
             'degrees':self.get_degrees_histogram,
             'rhythms':self.get_rhythms_histogram}

        if not measure.code in c:
            raise UnknownSimMeasure

        return (c[measure.code])()

    def get_incomplete_bars(self):
        ''' cherche les mesures incompletes (rythmes et silences qui ne matchent pas la signature rythmique)'''

        invalid = []
        lastTimesig = None

        all_bars = self.m21_stream.measures(numberStart=0,numberEnd=None)

        if not all_bars:
            print("WARNING : no bars found in voice")
            return

        measure_index = 1 # let's start counting from 1
        for m in all_bars:
            if m.timeSignature:
                lastTimesig = m.timeSignature

            if float(m.barDuration.quarterLength) != float(lastTimesig.beatCount):
                invalid.append(measure_index)

            measure_index+=1

        return invalid


# FIXME
class IncompleteBarsError(Exception):
    pass
