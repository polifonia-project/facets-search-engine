import jsonpickle
import music21 as m21

class Item:
    """
    Simplified representation of a musical event in a sequence of sounds
    """
    def __init__(self) :
        # From MEI encoding
        self.id = ""
        # Sound description
        self.step = "A"
        self.octave = 4
        self.alteration = 0
        # Duration of the item: the normalized representation (n times the DURATION_UNIT)
        self.duration = 4
        self.is_rest = False
        #self.is_grace=False
        self.tied = False
        # Lilypond duration: used to easily produce a PAE code from an item
        #self.pae_dur = 0
    
    def get_music21_note(self):
        """
        Transfer an Item into a Music21 note object with the step, octave and alteration values.
        """
        if self.alteration == 0:
            m21_note = self.step+str(self.octave)
        elif self.alteration == 1:
            m21_note = self.step+'#'+str(self.octave)
        elif self.alteration == -1:
            m21_note = self.step+'-'+str(self.octave)
        #Double alteration
        elif self.alteration == 2:
            m21_note = self.step+'##'+str(self.octave)
        elif self.alteration == -2:
            m21_note = self.step+'--'+str(self.octave)

        return m21.note.Note(m21_note)
        
    def decode(self, json_obj):
        """ Decode from a JSON object"""
        if "id" in json_obj:
            self.id = json_obj["id"]
        self.duration = json_obj["duration"]
        if json_obj["is_rest"] is True:
            self.is_rest = True
        else:
            self.step = json_obj["step"]
            self.octave = json_obj["octave"]
            self.alteration = json_obj["alteration"]
            self.tied = json_obj["tied"]
            #if ("isGrace" in json_obj):
            #    self.is_grace = json_obj["isGrace"]
            #self.pae_dur = json_obj["paeDur"]

    def encode(self):
        '''Encode in JSON'''
        return jsonpickle.encode(self, unpickable=True)
    
    def get_index(self):
        """
         Converts a note to an absolute integer value
        """
        # Count the number of semi tones from the lowest value
        result = 0
        result = self.octave * 12
        
        # Case by case decision
        if self.step == "A":
            result += 0
        elif self.step == 'B':
            result += 2
        elif self.step == 'C':
            result -= 9
        elif self.step == 'D':
            result -= 7
        elif self.step == 'E':
            result -= 5
        elif self.step == 'F':
            result -= 4
        elif self.step=='G':
            result -= 2
            
        # Alteration
        result += self.alteration
        
        return result

    def __str__(self):
        if self.alteration == 0:
            str_alter = ""
        else:
            str_alter = str(self.alteration)
 
        return self.step + str_alter + "/" + str(self.octave) + "-" + str(self.duration)
