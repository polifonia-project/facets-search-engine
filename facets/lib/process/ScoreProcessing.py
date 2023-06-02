"""
    Processing scores or zip of scores.

    Transform score to music21 stream to MusicSummary,
    get metadata, extract features.

"""

from lib.search.IndexWrapper import IndexWrapper
from lib.music.Score import *
from lib.music.MusicSummary import *
from lib.process.WikiComposer import *
from rest.models import *

from music21 import converter, mei
import zipfile
import json
import io
import os
from binascii import unhexlify
from django.core.files import File
from django.core.files.base import ContentFile
import xml.etree.ElementTree as ET
import re

def get_metadata_from_score(doctype, score, m21_score):
    """
    Get composer and title information directly from the scores
    """
    
    # TODO: clean the '\n's from composer names and title names. kern
    # TODO2: multiple composers by Music21

    metainfo = {"title": "", "composer": "", "period": ""}
    
    if doctype == "xml":

        root = ET.fromstring(score)
        # First, try to get title from music21 stream
        if m21_score.metadata.title != None and m21_score.metadata.title != "":
            metainfo["title"] = m21_score.metadata.title
        # If not from m21 stream, find title of the composition from XML score
        elif root.find('work/work-title') != None:
            metainfo["title"] = root.find('work/work-title').text
        elif root.find('work/title') != None:
            metainfo["title"] = root.find('work/title').text
        
        # Find composer info from m21 score
        if m21_score.metadata.composer != None and m21_score.metadata.composer != "":
            metainfo["composer"] = m21_score.metadata.composer 
        elif root.find('identification/creator') != None:
            allcreators = root.findall('identification/creator')
            for item in allcreators:
                # First find the item with attrib as composer
                # if there is more than one marked as composer, we take the first one.
                if item.attrib == {'type': 'composer'} and metainfo["composer"] == "":
                    metainfo["composer"] = item.text
                #if item.attrib == {'type': 'lyricist'}:
                    # lyricist could be save in metadata in the future
            # If there is only one creator and there is no attrib, we consider this creator as the composer.
            if len(allcreators) == 1 and allcreators[0].attrib == {} and metainfo["composer"] == "":
                metainfo["composer"] = allcreators[0].text
        elif root.find('identification/composer') != None:
            metainfo["composer"] = root.find('identification/composer').text

    elif doctype == "musicxml":

        # Element Tree does not work for MusicXML, so find it in m21 stream first
        if m21_score.metadata.title != None and m21_score.metadata.title != "":
            metainfo["title"] = m21_score.metadata.title
        else:
            # If not found in m21, try find it in musicxml file
            worktitles = re.findall('<work-title.*>(.*)</work-title>', score)
            if worktitles != []:
                # Found: <work-title>TITLE</work-title>
                metainfo["title"] = worktitles[0]
            elif score.find('key="OTL"') != -1:
                # work-title not found, but found title in comments
                worktitles = re.findall('key="OTL".*value="(.*)"', score)
                if worktitles != []:
                    # found: <!-- INFO key="OTL" value="TITLENAME" -->
                    metainfo["title"] = worktitles[0]

        # Find composer info
        if m21_score.metadata.composer != None and m21_score.metadata.composer != "":
            # found composer in m21 stream
            metainfo["composer"] = m21_score.metadata.composer
        else:
            composernames = re.findall('<creator.*type="composer".*>(.*)</creator>', score)
            if composernames != []:
                # found creator with a composer tag
                metainfo["composer"] = composernames[0]
            else:
                composernames = re.findall('<creator>(.*)</creator>', score)
                if composernames != []:
                    # found creator without any tag
                    metainfo["composer"] = composernames[0]
                else:
                    composernames = re.findall('<creator.*type="creator".*>(.*)</creator>', score)
                    if composernames != []:
                        metainfo["composer"] = composernames[0]
            if metainfo["composer"] == "" and score.find('key="COM"') != -1:
                # found composer info in comments
                composernames = re.findall('key="COM".*value="(.*)"', score)
                if composernames != []:
                    metainfo["composer"] = composernames[0]
    
    elif doctype == "mei":
        # Note: there might be more than one title, currently we get the first one

        if m21_score.metadata.title != None and m21_score.metadata.title != "":
            metainfo["title"] = m21_score.metadata.title
        else:
            # First find title with label as work
            worktitles = re.findall('<title label="work".*>(.*)<', score)
            if worktitles == []:
                # If not found, find title without any label
                worktitles = re.findall('<title>(.*)</title>', score)
                if worktitles == []:
                    # If still not found, then find title with irrelevant labels...
                    worktitles = re.findall('<title .*>(.*)</title>', score)
            if worktitles != []:
                # if found any, record the title info
                metainfo["title"] = worktitles[0]

        if m21_score.metadata.composer != None and m21_score.metadata.composer != "":
            # found composer info in m21 stream
            metainfo["composer"] = m21_score.metadata.composer
        else:
            # try to find <name role="composer">SOMEONE</name>
            composernames = re.findall('<name.*role="composer".*>(.*)</name>', score)
            if composernames == []:
                # try to find <persName role="composer">SOMEONE</persName>
                composernames = re.findall('<persName.*role="composer".*>(.*)</persName>', score)
                if composernames == []:
                    # <persName role="creator" codedval="12345">SOMEONE</persName>
                    composernames = re.findall('<persName.*role="creator".*>(.*)</persName>', score)
            if composernames != []:
                metainfo["composer"] = composernames[0]

        """
        # Element Tree does not work for MEI! Otherwise title could be found this way:
        if root.find('meiHead/fileDesc/titleStmt/title') != None:
            metainfo["title"] = root.find('meiHead/fileDesc/titleStmt/title').text
        elif root.find('meiHead/fileDesc/sourceDesc/source/titleStmt/title') != None:
            metainfo["title"] = root.find('meiHead/fileDesc/sourceDesc/source/titleStmt/title').text
        """

    elif doctype == "krn":
        if m21_score.metadata.title != None and m21_score.metadata.title != "":
            metainfo["title"] = m21_score.metadata.title
        elif score.find('!!!OTL:') != -1:
            startpos = score.find('!!!OTL:')
            endpos = score.find('\n', startpos+7)
            if startpos != -1 and endpos != -1 and startpos+7 < endpos:
                metainfo["title"] = score[startpos+7:endpos]

        if m21_score.metadata.composer != None and m21_score.metadata.composer != "":
            metainfo["composer"] = m21_score.metadata.composer
        elif score.find('!!!COM:') != -1:
            # found composer information
            startpos = score.find('!!!COM:')
            endpos = score.find('\n', startpos+7)
            if startpos != -1 and endpos != -1 and startpos+7 < endpos:
                metainfo["composer"] = score[startpos+7:endpos]

    elif doctype == "abc":
        # Get title info
        if m21_score.metadata.title != None and m21_score.metadata.title != "":
            metainfo["title"] = m21_score.metadata.title
        else:
            # if not in m21 stream, directly find in score
            titlestart = score.find('T:')
            if titlestart != -1:
                # found title in ABC score
                end_pos = score.find('\n', titlestart)
                metainfo["title"] = score[titlestart+2:end_pos]

        # Get composer info
        if m21_score.metadata.composer != None and m20_score.metadata.composer != "":
            metainfo["composer"] = m21_score.metadata.composer
        else:
            # if not in m21, directly find in score
            compstart = score.find('C:')
            if compstart != -1:
                # found composer in ABC score
                end_pos = score.find('\n', compstart)
                metainfo["composer"] = score[compstart+2:end_pos]

    # print for testing
    if metainfo["title"] != "":
        print("Title of this musicdoc:", metainfo["title"])
    else:
        metainfo["title"] = "Unknown title"
        print("Couldn't find title information of this musicdoc.")

    if metainfo["composer"] != "":
        print("Composer of this musicdoc:", metainfo["composer"])
        try:
            compo = WikiComposer(metainfo["composer"])
            print("----- INFO -----")
            print(compo.info)
            if "dob" in compo.info:
                dateofbirth = compo.info["dob"]
                yearofbirth = int(dateofbirth.split('-')[0])
                metainfo["period"] = str(int(yearofbirth/100))+"century"
            if 'dod' in compo.info:
                dateofdeath = compo.info["dod"]
                yearofdeath = int(dateofdeath.split('-')[0])
                if metainfo["period"] != "":
                    # another century add to period
                    if int(yearofbirth/100) != int(yearofdeath/100):
                        metainfo["period"] += " to "+str(int(yearofdeath/100))+"century"
                else:
                    metainfo["period"] = str(int(yearofdeath/100))+"century"
                print("period:", metainfo["period"])
        except:
            print("Can not get more info of this composer through wikidata.")

    else:
        metainfo["composer"] = "Unknown composer"
        print("Couldn't find composer information of this musicdoc.")

    return metainfo

"""
# this is metadata for corpus but we need metadata for single files
def load_meta_from_json(dict_corpus):
        # For zip, filter out the metadata we don't need(?) 
        metainfo = {"title":"", "composer":""}
        # Should this be empty? sometimes they can be extracted from score
    
        metainfo["title"] = dict_corpus["title"]
        #metainfo["short_title"] = dict_corpus["short_title"]
        metainfo["description"] = dict_corpus["description"]
        #metainfo["short_description"] = dict_corpus["short_description"]
        #metainfo["is_public"] = dict_corpus["is_public"]
        if "copyright" in dict_corpus:
            metainfo["copyright"] = dict_corpus["copyright"]
        if "supervisors" in dict_corpus:
            metainfo["supervisors"] = dict_corpus["supervisors"]
        return metainfo
"""

def save_data(index_name, docid, doctype, score, m21_score):

        # If there is no such index, create such index and store the score
        if Index.objects.filter(name=index_name).exists():
            index = Index.objects.get(name = index_name)
        else:
            index = Index()
            index.name = index_name
            index.save()

        # Delete musicdoc object saved in database of the same id, if exists
        MusicDoc.objects.filter(doc_id=docid).delete()

        # Create a musicdoc object
        musicdoc = MusicDoc()
        musicdoc.index = index
        musicdoc.doc_id = docid
        musicdoc.doc_type = doctype
        musicdoc.m21score = m21_score

        # Get and save metadata(title and composer so far)
        # TODO: include the extract info into get_metadata_from_score
        try:
            # get title, composer, period information here
            metainfo = get_metadata_from_score(doctype, score, m21_score)
        except:
            # in case there is an error, just skip and leave these fields empty
            metainfo = {"title":"Unknown title", "composer":"Unknown composer"}

        if metainfo["title"] != '':
            musicdoc.title = metainfo["title"]
        if metainfo["composer"] != '':
            if Person.objects.filter(name=metainfo["composer"]).exists():
                curr_composer = Person.objects.get(name = metainfo["composer"])
                # if there's no period info and we get period info, update it 
                if curr_composer.period == None and metainfo['period'] != '':
                    curr_composer.period = metainfo['period']
                    print("Updating period info of composer:",metainfo["composer"])
                    curr_composer.save()
                musicdoc.composer = curr_composer
                musicdoc.save()
            else:
                curr_composer = Person()
                curr_composer.name = metainfo["composer"]
                if metainfo['period'] != '':
                    curr_composer.period = metainfo['period']
                curr_composer.save()
                musicdoc.composer = curr_composer
                musicdoc.save()
        elif Person.objects.filter(name="Unknown composer").exists():
            musicdoc.composer = Person.objects.get(name = "Unknown composer")
        else:
            curr_composer = Person()
            curr_composer.name = "Unknown composer"
            curr_composer.save()
            musicdoc.composer = curr_composer
        
        # Save file
        filename = docid+"."+doctype
        if doctype == 'krn':
            musicdoc.krnfile.save(filename, ContentFile(score))
        elif doctype == 'musicxml':
            musicdoc.musicxmlfile.save(filename, ContentFile(score))
        elif doctype == 'mei':
            musicdoc.meifile.save(filename, ContentFile(score))
        elif doctype == 'xml':
            musicdoc.xmlfile.save(filename, ContentFile(score))
        elif doctype == 'abc':
            musicdoc.abcfile.save(filename, ContentFile(score))

        musicdoc.save()

        return musicdoc

def extract_features(score, music_summary, musicdoc):

        descr_dict = {}
        try:
                types = "chromatic", "diatonic", "rhythmic", "lyrics", "notes"
                for atype in types:
                    descr_dict[atype] = {}

                # Delete the descriptor of the same musicdoc if exists in the database
                Descriptor.objects.filter(doc=musicdoc).delete()
                
                #Iterate over all the parts of MusicSummary
                for part_id, curr_part in music_summary.parts.items():

                    #Iterate over all the voices of this part
                    for voice_id, curr_voice in curr_part.items():
                        
                        """
                            Extract chromatic interval feature
                        """
                        chr_descr = curr_voice.get_chromatic_encoding()

                        # Descriptor object
                        descriptor = Descriptor()
                        descriptor.doc = musicdoc
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.descr_type = "chromatic"
                        descriptor.value = chr_descr

                        #save part + voice + value info of the descriptor to descr_dict
                        descr_dict["chromatic"][str(voice_id)] = descriptor.to_dict()
                        #If we do not use descriptor object:
                        ##descr_dict["chromatic"][str(voice_id)] = dict(part=part_id, voice=voice_id, value=chr_descr)
        
                        """
                            Extract diatonic interval feature
                        """

                        dia_descr = curr_voice.get_diatonic_encoding()
                        
                        descriptor = Descriptor()
                        descriptor.doc = musicdoc
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.descr_type = "diatonic"
                        descriptor.value = dia_descr

                        # Save to descriptor dictionary for indexing
                        descr_dict["diatonic"][str(voice_id)] = descriptor.to_dict()

                        """
                            Extract rhythmic interval feature
                        """
                        rhy_descr = curr_voice.get_rhythm_encoding()

                        descriptor = Descriptor()
                        descriptor.doc = musicdoc
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.descr_type = "rhythmic"
                        descriptor.value = rhy_descr

                        # Save to descriptor dictionary for indexing
                        descr_dict["rhythmic"][str(voice_id)] = descriptor.to_dict()

                        """
                            Extract notes features for exact search
                        """
                        notes_descr = curr_voice.get_note_encoding()

                        descriptor = Descriptor()
                        descriptor.doc = musicdoc
                        descriptor.part = part_id
                        descriptor.voice = voice_id
                        descriptor.descr_type = "notes"
                        descriptor.value = notes_descr

                        # Save to descriptor dictionary for indexing
                        descr_dict["notes"][str(voice_id)] = descriptor.to_dict()
                
                """
                    Extract lyrics feature
                    Attention: this works and only works for MusicXML files!
                    To be improved for other formats...
                """

                #  Get a list of Voice objects from the current Score object
                all_voices = score.get_all_voices()
                for this_voice in all_voices:
                    #  "this_voice" is different from the previous "curr_voice":
                    # "this_voice" is a Voice object. 
                    if this_voice.has_lyrics():
                        # Get lyrics from the Voice object
                        lyrics_descr = this_voice.get_lyrics()

                        descriptor = Descriptor()
                        descriptor.doc = musicdoc
                        descriptor.voice = this_voice.id
                        descriptor.descr_type = "lyrics"
                        descriptor.value = lyrics_descr

                        # Save to descriptor dictionary for indexing
                        descr_dict["lyrics"][str(this_voice.id)] = descriptor.to_dict()

        except Exception as ex:
            print ("Exception when trying to write descriptor" + musicdoc.doc_id + " Message:" + str(ex))

        return descr_dict


def extract_info_from_score(m21_score):
    
    info = {}
    
    key = m21_score.analyze('key')
    info["key_tonic_name"] = key.tonic.name
    info["key_mode"] = key.mode
    info["key"] = info["key_tonic_name"]+" "+info["key_mode"] 

    info["num_of_parts"] = len(m21_score.getElementsByClass(stream.Part))
    #info["num_of_voices"] = len(m21_score.getElementsByClass(stream.Voice))
    info["num_of_measures"] = 0
    for part in m21_score.parts:
        info["num_of_measures"] += len(part)

    info["num_of_notes"] = len(m21_score.flatten().getElementsByClass(note.Note))

    info["instruments"] = []
    if instrument.partitionByInstrument(m21_score) != None:
        for part in instrument.partitionByInstrument(m21_score):
            # part.getInstrument() is a music21 object
            info["instruments"].append(part.getInstrument().instrumentName)
    if info["instruments"] == []:
        info["instruments"].append("Unknown instrument")
    
    #print("Pitch analysis:")
    nameCount = analysis.pitchAnalysis.pitchAttributeCount(m21_score, 'name')
    dict_common_pitch = {}
    #print("10 most common pitch and occurrence:")
    for n, count in nameCount.most_common(10):
    #   print("%2s: %2d" % (n, nameCount[n]))
        dict_common_pitch[n] = nameCount[n]
    info["most_common_pitches"] = json.dumps(dict_common_pitch)

    """
    pcCount = analysis.pitchAnalysis.pitchAttributeCount(m21_score, 'pitchClass')
    # can use nameWithOctave or name
    for n in sorted(pcCount):
        print("%2d notes in pitch class%2d" % (pcCount[n] , n))
    """

    pitchmin_eachpart = {}
    pitchmax_eachpart = {}
    p = analysis.discrete.Ambitus()
    count = 0
    for part in m21_score.parts:
        count += 1
        pitchMin, pitchMax = p.getPitchSpan(part)
        partname = 'part'+str(count)
        pitchmin_eachpart[partname] = pitchMin.nameWithOctave
        pitchmax_eachpart[partname] = pitchMax.nameWithOctave
        #print("Lowest pitch of part", count, "is ", pitchMin.nameWithOctave)
        #print("Highest pitch of part", count, "is ", pitchMax.nameWithOctave)
    
    info["lowest_pitch_each_part"]  = json.dumps(pitchmin_eachpart)
    info["highest_pitch_each_part"]  = json.dumps(pitchmax_eachpart)

    # pitch histogram?
    #fe = features.jSymbolic.BasicPitchHistogramFeature(m21_score)

    """
    The following ones require a few seconds to run for each scores..
    """
    fe = features.jSymbolic.AverageMelodicIntervalFeature(m21_score)
    #print("Average melodic interval in semitones:", fe.extract().vector[0])
    info["average_melodic_interval"] = fe.extract().vector[0]

    fe = features.jSymbolic.DirectionOfMotionFeature(m21_score)
    #print("Direction of motion (the fraction of melodic intervals that are rising rather than falling):", fe.extract().vector[0])
    info["direction_of_motion"] = fe.extract().vector[0]

    #print("\nNote length analysis:")

    fe = features.native.MostCommonNoteQuarterLength(m21_score)
    #print("Most common note quarter length:", fe.extract().vector[0])
    info["most_common_note_quarter_length"] = fe.extract().vector[0]

    fe = features.native.RangeOfNoteQuarterLengths(m21_score)
    #print("Difference between the longest and shortest quarter lengths:", fe.extract().vector[0])
    info["range_note_quarter_length"] = fe.extract().vector[0]

    """
    # jSymbolic number should be *2 to be consistent with other "note quarter lengths" features
    fe = features.jSymbolic.MaximumNoteDurationFeature(m21_score)
    print("Duration of the longest note:", fe.extract().vector[0])

    fe = features.jSymbolic.MinimumNoteDurationFeature(m21_score)
    print("Duration of the shortest note:", fe.extract().vector[0])

    fe = features.jSymbolic.AverageNoteDurationFeature(m21_score)
    print("Average note duration:", fe.extract().vector[0])
    """

    fe = features.jSymbolic.InitialTimeSignatureFeature(m21_score)
    #print("\nInitial time signature:", fe.extract().vector)
    init_timesig = fe.extract().vector
    # If it is [0,0], then it should be considered as default time signature 4/4
    if init_timesig[0] == 0 and init_timesig[1] == 0:
        init_timesig[0] = 4
        init_timesig[1] = 4
    # change the format to string
    str_timesig = str(init_timesig[0])+'/'+str(init_timesig[1])
    #info["initial_time_signature"] = json.dumps(init_timesig)
    info["initial_time_signature"] = str_timesig

    print("Info of the score:", info)

    # Get diatonic scale degree
    midi_note = [] # not necessary
    diatonic_note_num = []
    pitch_class = []
    diatonic_scale_degree = []

    # Getting midi pitch value for each note, pitch class and diatonic note number
    for thisnote in m21_score.recurse().notes:
        if thisnote.isNote:
            midi_note.append(float(thisnote.pitch.ps))
            diatonic_note_num.append(float(thisnote.pitch.diatonicNoteNum))
            pitch_class.append(float(thisnote.pitch.pitchClass))
            # if chords are encountered, take their root: (this is rare in our corpora)
        elif thisnote.isChord:
            # if it is a chord, only take the root
            midi_note.append(float(thisnote.root().ps))
            diatonic_note_num.append(float(thisnote.root().diatonicNoteNum))
            pitch_class.append(float(thisnote.root().pitchClass))

    # Diatonic root of the score
    diatonic_root = key.tonic.diatonicNoteNum

    # Calcuate diaotnic scale degree of each note and save in a list
    for note_num in diatonic_note_num:
        relative_diatonic_pitch = note_num - diatonic_root
        temp = int(relative_diatonic_pitch % 7) + 1
        diatonic_scale_degree.append(temp)

    # A list of numbers from 1 to 7 representing diatonic scale degree of each note
    # Let's not save it to ES yet! Commented the next line
    # If we want to save it to ES, need to update allowed list in model.py
    #info["diatonic_scale_degree"] = diatonic_scale_degree
    #print("diatonic_scale_degree_of_this_score:", diatonic_scale_degree)

    return info

def decompose_zip_name(fname):

    dirname = os.path.dirname(fname)
    dircomp = dirname.split(os.sep)
    basename = os.path.basename(fname)
    components = os.path.splitext(basename) 
    extension = components[len(components)-1]
    opus_ref = ""
    sep = ""
    for i in range(len(components)-1):
        if i > 0:
            sep = "-"
        opus_ref += components[i] + sep
    return (opus_ref, extension)

def read_zip(index_name, byte_str):
        """
            Load all scores in zip file, check name and formats.
            Create and save a set of musicdoc objects for all supported scores.
            Also get music21 stream of these scores.

            A zipfile should contain at least one music scores in the format supported(mei, musicxml etc.)
            
            Note: codes of import zip are partially migrated from neuma/manager/models.py
        """
        
        b = io.BytesIO(byte_str)

        zfile = zipfile.ZipFile(b, "r")

        valid_namelist = []
        m21scores = {}
        musicdocs = {}
        all_metas = {}

        for fname in zfile.namelist():
            # Skip files with weird names
            base, extension = decompose_zip_name(fname)
            
            # base is file name, will be used as doc_id, extension is the file format
            if base == "" or base.startswith('_') or base.startswith('.'):
                continue

            # TODO: if there is a folder within zip, work with it

            # Read json
            if extension == ".json":
                # should check name of the json file to know if it is for a single score or the whole zip...
                # store in a dict called all_metas for loading later
                meta_dict = json.loads(zfile.read(fname).decode('utf'))
                #metainfo_zip = load_meta_from_json(meta_dict)
                all_metas[base] = meta_dict
                #print(all_metas[base])
                print("Found a metadata file:%s%s" % (base, extension))

            if (extension == ".mei" or extension == ".xml"
                or extension=='.krn' or extension=='.abc' or extension == '.musicxml'): #or extension == '.mxl' 
                valid_namelist.append(fname)
            else:
                print ("Ignoring file %s.%s" % (base, extension))

        for valid_name in valid_namelist:
            base, extension = decompose_zip_name(valid_name)
            cur_file = zfile.read(valid_name)
            cur_file = cur_file.decode('utf')

            m21_score, musicdoc = load_score(index_name, cur_file, extension[1:], base)

            if m21_score == "" and musicdoc == None:
                # In case there are broken scores in zip, skip the score instead of raising error
                print("Error when loading the current score:", extension[1:], base)
            else:
                print("Successfully loaded and saved the score:", valid_name)
                m21scores[base] = m21_score
                musicdocs[base] = musicdoc
        
        return m21scores, musicdocs, all_metas

def load_and_process_zip(index_name, byte_str):

        """
        Check validity and get content by calling read_zip(), 
        which includes getting m21 streams and musicdoc objects saved in database by calling load_score().
        Then extract features and get MusicSummary,
        and finally index them in ES.
        """
        m21scores = {}
        musicdocs = {}
        valid_score_ids = []

        try:
            m21scores, musicdocs, all_metas = read_zip(index_name, byte_str)
        except Exception as ex:
            print ("Exception when trying to call read_zip()" + " Message:" + str(ex))

        if m21scores == {}:
            # there is a problem: no score was successfully loaded.
            return True
        else:
            # Process the current score, produce descriptors from MusicSummary
            for score_id in m21scores:
                try:
                    # Get MusicSummary and extracted descriptors
                    descr_dict, encodedMS, extracted_infos = process_score(musicdocs[score_id], m21scores[score_id], score_id)

                    # Index the current musicdoc, including id, musicsummary and its descriptors in "index_name" index
                    index_wrapper = IndexWrapper(index_name) 
                    index_wrapper.index_musicdoc(index_name, musicdocs[score_id], descr_dict, encodedMS, extracted_infos)
                    # in case needed for metadata loading
                    print("Successfully indexed the current document: ", score_id)

                    valid_score_ids.append(score_id)
                except:
                    print("Ignoring score", score_id, ", error occurred while processing")
                    continue
            try:
                if all_metas != {} and all_metas != None:
                    load_meta_from_zip(index_name, all_metas, valid_score_ids)
            except Exception as ex:
                print ("Exception when trying to load metadata" + " Message:" + str(ex))

            # if no error occured, return False
            return False

def load_meta_from_zip(index_name, all_metas, valid_score_ids):
        """
            Load metadata from zip:
            the json files named doc_id would be added as metadata of doc
            the json files named corpus: currently, we take the composer info and add to all docs in zip 
        """
        invalid_composer_names = ['Unknown composer', 'Unknown', 'unknown', '']
        need_update_on_ES = False
        indexwrapper = IndexWrapper(index_name)
        for name in all_metas:
                # first get composer info
                if 'composer' not in all_metas[name]:
                    continue
                composer_info_dict = all_metas[name]["composer"]
                if composer_info_dict == None or composer_info_dict == {}:
                    continue
                # If there is composer info to update:
                # find person in database
                curr_composer = None
                if 'first_name' in composer_info_dict and 'last_name' in composer_info_dict:
                    composerfullname = composer_info_dict["first_name"] + " " + composer_info_dict["last_name"]
                elif 'name' in composer_info_dict:
                    composerfullname = composer_info_dict['name']
                if composerfullname not in invalid_composer_names:
                    # otherwise not add to database
                    if Person.objects.filter(name=composerfullname).exists():
                        # get the Person object by name
                        curr_composer = Person.objects.get(name = composerfullname)
                        # update the info in case they are missing:
                        if curr_composer.year_birth == None or curr_composer.year_birth == "":
                            if "year_birth" in composer_info_dict:
                                curr_composer.year_birth = composer_info_dict["year_birth"]
                                birthcentury = int(composer_info_dict["year_birth"]/100)
                                curr_composer.period = str(birthcentury)+"century"
                                print("year of birth:", yearofbirth)
                                print("Updated Person:", curr_composer.name, "'s period")
                        if curr_composer.year_death == None or curr_composer.year_death == "":
                            if "year_death" in composer_info_dict:
                                curr_composer.year_death = composer_info_dict["year_death"]
                                deathcentury = int(composer_info_dict["year_death"]/100)
                                if curr_composer.period != None and curr_composer.period != "":
                                    if "year_birth" in composer_info_dict:
                                        # if there is birth year
                                        if birthcentury!=deathcentury:
                                            # if year birth and year death are in dif centuries.
                                            curr_composer.period += " to "+str(deathcentury)+"century"
                                else:
                                    #if there's no birth year info, only death year info
                                    curr_composer.period = str(deathcentury)+"century"
                                print("Updated Person:", curr_composer.name, "'s period")
                        if curr_composer.country == None or curr_composer.country == "":
                            if "country" in composer_info_dict:
                                curr_composer.country = composer_info_dict["country"]
                                print("Updated Person:", curr_composer.name, "'s country")
                        if curr_composer.wikidata_url == None or curr_composer.wikidata_url == "":
                            if "dbpedia_uri" in composer_info_dict:
                                curr_composer.wikidata_url = composer_info_dict["dbpedia_uri"]
                                print("Updated Person:", curr_composer.name, "'s url")
                            elif "wikidata_url" in composer_info_dict:
                                curr_composer.wikidata_url = composer_info_dict["wikidata_url"]
                                print("Updated Person:", curr_composer.name, "'s url")
                        curr_composer.save()
                    else:
                        # if not exist, create this person in database
                        curr_composer = Person()
                        curr_composer.name = composerfullname
                        if "year_birth" in composer_info_dict:
                            curr_composer.year_birth = composer_info_dict["year_birth"]
                            birthcentury = int(composer_info_dict["year_birth"]/100)
                            curr_composer.period = str(birthcentury)+"century"
                        if "year_death" in composer_info_dict:
                            curr_composer.year_death = composer_info_dict["year_death"]
                            deathcentury = int(composer_info_dict["year_death"]/100)
                            if curr_composer.period != None and curr_composer.period != "":
                                if "year_birth" in composer_info_dict:
                                    if birthcentury != deathcentury:
                                        # if year birth and year death are in dif centuries.
                                        curr_composer.period += " to "+str(int(yearofdeath/100))+"century"
                            else:
                                #if there's no birth year info, only death year info
                                curr_composer.period = str(deathcentury)+"century"
                        if "country" in composer_info_dict:
                            curr_composer.country = composer_info_dict["country"]
                        if "dbpedia_uri" in composer_info_dict:
                            curr_composer.wikidata_url = composer_info_dict["dbpedia_uri"]
                        print("Creating new Person:", composerfullname)
                        curr_composer.save()
                else:
                    # invalid composer, not add as metadata
                    continue

                # Now add composer information to database,
                # if the json file name is corpus, add composer info for all the files in this zip
                if name == "corpus" and curr_composer != None:
                    # add composer info for all scores in the zip
                    for doc_id in valid_score_ids:
                        musicdoc = MusicDoc.objects.get(doc_id=doc_id)
                        if musicdoc.composer != None:
                            checkcomposer = musicdoc.composer
                            if checkcomposer.name not in invalid_composer_names:
                                print("There's already composer info, ignoring adding corpus metadata to:", doc_id)
                            else:
                                # There was no composer info for this musicdoc, thus add metadata
                                musicdoc.composer = curr_composer
                                musicdoc.save()
                                # update the ES as well
                                docMS = indexwrapper.get_MS_from_doc(index_name, doc_id)
                                if docMS == None:
                                    print("Error: can't find file when trying to update metadata on ES.")
                                else:
                                    try:
                                        indexwrapper.update_musicdoc_metadata(index_name, doc_id, musicdoc)
                                        print("Updating metadata of doc:", doc_id, "using corpus.json")
                                    except Exception as ex:
                                        print("Error while updating musicdoc metadata: ", doc_id, ":", str(ex))
                        else:
                            indexwrapper.update_musicdoc_metadata(index_name, doc_id, musicdoc)
                            print("Updating metadata of doc:", doc_id, "using corpus.json")

                elif name in valid_score_ids and curr_composer != None:
                    # add metadata info if the score is in database and there's composer info available
                    musicdoc = MusicDoc.objects.get(doc_id=name)
                    if musicdoc.composer != None:
                        checkcomposer = musicdoc.composer
                        if checkcomposer.name not in invalid_composer_names:
                            print("There's already composer info, ignoring adding corpus metadata to:", doc_id)
                        else:
                            # There was no composer info for this musicdoc, thus add metadata
                            musicdoc.composer = curr_composer
                            musicdoc.save()
                            docMS = indexwrapper.get_MS_from_doc(index_name, doc_id)
                            if docMS == None:
                                print("Error: can't find file when trying to update metadata on ES.")
                            else:
                                indexwrapper.update_musicdoc_metadata(index_name, name, musicdoc)
                                print("Updating metadata of doc:", doc_id, "using corpus.json")
                    else:
                        # otherwise update the musicdoc metadata with given info in corpus.json
                        indexwrapper.update_musicdoc_metadata(index_name, name, musicdoc)
                        print("Updating metadata of doc:", doc_id, "using corpus.json")

        print("Successfully added metadata info to files in the zip")
        return

def load_score(index_name, score, s_format, docid):
        """
            Load a music score and save in database
        """

        if s_format != "mei" and s_format != "xml" and s_format != "krn" and s_format != "abc" and s_format != "musicxml": #and s_format != "mid": #need to work on midi
            print("Document format not supported for loading the current score.")
            return "", None
        
        # The original score -> M21 score
        if s_format == "mei":
            conv = mei.MeiToM21Converter(score)
            try:
                m21_score = conv.run()
            except:
                print("Error when loading the current score with music21: ", docid)
                return "", None
            
            musicdoc = save_data(index_name, docid, s_format, score, m21_score)

            return m21_score, musicdoc

        elif s_format == "xml" or s_format == "krn" or s_format == "musicxml" or s_format == "mid":
            try:
                m21_score = converter.parse(score)
            except:
                print("Error when loading the current score with music21: ", docid)
                return "", None
            
            musicdoc = save_data(index_name, docid, s_format, score, m21_score)

            return m21_score, musicdoc

        elif s_format == "abc":
            try:
                handler = abcFormat.ABCHandler()
                handler.process(score)
                m21_score = m21.abcFormat.translate.abcToStreamScore(handler)
            except:
                print("Error when loading the current score with music21: ", docid)
                return "", None

            musicdoc = save_data(index_name, docid, s_format, score, m21_score)
            
            return m21_score, musicdoc
        
def process_score(musicdoc, m21_score, doc_id):
        """
            From original score file to Score object, to MS object then extract features
            return musicdoc object, extracted features and MS, for indexing
        """

        try:
            # Create a Score object
            score = Score()
            # Get a Score object from m21stream of the score. 
            score.load_component(m21_score)
        except Exception as ex:
            print("Error while loading the score ", doc_id, " using music21: ", str(ex))
        
        try:
            # Get MusicSummary from Score object
            MS = score.get_music_summary()
            MS.doc_id = doc_id
            encodedMS = MS.encode()
        except Exception as ex:
            print("Error while encoding the score: ", doc_id, ":", str(ex))

        try:

            # Extract infos from the score
            extracted_infos = extract_info_from_score(m21_score)

            # add composer and period info as well
            if musicdoc.title:
                extracted_infos["title"] = musicdoc.title
            if musicdoc.composer.name:
                extracted_infos["composer"] = musicdoc.composer.name
            if musicdoc.composer.period != None:
                extracted_infos["period"] = musicdoc.composer.period

            # Save extracted info in the database
            # Ideally the data shouldn't be saved twice for loading of each score, but deal with it later.

            try:
                for item in extracted_infos:
                    musicdoc.add_info(item, extracted_infos[item])
                musicdoc.save()

            except Exception as ex:
                print ("Exception for musicdoc" + musicdoc.doc_id + " Message:" + str(ex))

            # Feature extraction
            descr_dict = extract_features(score, MS, musicdoc)
        except Exception as ex:
            print("Error while extracting features from ", doc_id, ":",str(ex))

        return descr_dict, encodedMS, extracted_infos
