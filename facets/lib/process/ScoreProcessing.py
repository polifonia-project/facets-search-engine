"""
	Processing scores or zip of scores.

	Transform score to music21 stream to MusicSummary,
	Then extract features.

"""

from lib.search.IndexWrapper import IndexWrapper
from lib.music.Score import *
from lib.music.MusicSummary import *
from rest.models import *

from music21 import converter, mei
import zipfile
import json
import io
import os
from binascii import unhexlify
from django.core.files import File
from django.core.files.base import ContentFile

def get_metadata_from_score(m21_score):
	# To do, not urgent
	"""
    # Get info from the text, something like below, or find a better solution
	if "composer" in search_input:
		self.pattern = search_input["pattern"]

	From MEI scores:
	 <meiHead>
      <fileDesc>
      <title label="work">I, 1. Bransle simple. Bis</title>
       <name role="composer">Franc. Caroubel.</name>

    From XML scores:
	<work>
		<work-title>Les Baricades Misterieuses</work-title>
	</work>
	<identification>
	<creator type="composer">Francois Couperin</creator>
	

	From ABC scores:
	!!!OTL: SYV SPRING
	!!!ARE: Europa, Mitteleuropa, Daenemark, Vendsyssel
	The title field (T:) and the index field (X:)
	Nearly every tune has a title, and one should always be included for identification purposes in tune lists, even if the exact title is not known. The title is indicated by the T: field eg

	T:Ballydesmond polka
	More (optional) fields : composer, source, origin, notes
	The composer of a tune is recorded in the C: field, eg

	T:Paddy O'Rafferty
	C: Mozart.

	For MusicXML:
	<work>
    	<work-number>D. 911</work-number>
    	<work-title>Winterreise</work-title>
    </work>
  	<identification>
    	<creator type="composer">Franz Schubert</creator>
  	</identification>

<!-- INFO key="COM" value="Gaspar van Weerbeke" -->
<!-- INFO key="CDT" value="~1450-~1517" -->
<!-- INFO key="OPR" value="Motet cycle Ave mundi domina" -->
<!-- INFO key="OTL" value="Quem terra, ponthus, aethera" -->
<!-- INFO key="OMV" value="6" -->
<!-- INFO key="AGN" value="Motet; Motet cycle" -->
<!-- INFO key="SCT" value="Gas0301f" -->
<!-- INFO key="SCA" value="Gas0301f" -->
<!-- INFO key="voices" value="4" -->

	For kern scores:

!!!AGN: Tanz - Lied, Reigen, Siebensprung
!!!ONB: ESAC (Essen Associative Code) Database: ERK2
!!!AMT: simple duple
!!!AIN: vox
!!!EED: Helmut Schaffrath
!!!EEV: 1.0
!!!OTL: SYV SPRING
!!!ARE: Europa, Mitteleuropa, Daenemark, Vendsyssel
!!!SCT: E0992C
!!!YEM: Copyright 1995, estate of Helmut Schaffrath.

	- some has their own part id in xml, what do we do about it here
	- How about multiple composers?
	- Allow this information to be blank

	For MIDI: how?
	"""
	return

def save_data(index_name, docid, doctype, score, m21_score):

		# TODO: get and save metadata
		get_metadata_from_score(m21_score)

		if Index.objects.filter(name=index_name).exists():
			index = Index.objects.get(name = index_name)
		else:
			index = Index()
			index.name = index_name
			index.save()

		# Delete musicdoc object saved in database of the same id if exists
		MusicDoc.objects.filter(doc_id=docid).delete()
	 	# Create a musicdoc object
		musicdoc = MusicDoc()
		musicdoc.index = index
		musicdoc.doc_id = docid
		musicdoc.doc_type = doctype
		musicdoc.m21score = m21_score

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
					Attention: this may only work for musicXML files!!
					To be checked...
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
						descriptor.part = part_id
						descriptor.voice = voice_id
						descriptor.descr_type = "lyrics"
						descriptor.value = lyrics_descr

						# Save to descriptor dictionary for indexing
						descr_dict["lyrics"][str(voice_id)] = descriptor.to_dict()

		except Exception as ex:
			print ("Exception when trying to write descriptor" + musicdoc.doc_id + " Message:" + str(ex))

		return descr_dict

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
		"""
		# May improve later: work with json metadata, cover pictures.
		files = {}
		found_corpus_data = False
		found_cover = False
		corpus_dict = {}
		cover_data = ""
		"""

		for fname in zfile.namelist():
			# Skip files with weird names
			base, extension = decompose_zip_name(fname)
			# base is file name, will be used as doc_id, extension is the file format
			if base == "" or base.startswith('_') or  base.startswith('.'):
				continue

			# TODO: if there is a folder within zip, work with it

			"""
			# Look for the data file in json format
			if extension == ".json":
				# not in use now since we do not support json metadata yet
				found_corpus_data = True 
				corpus_dict = json.loads(zfile.open(fname).read().decode('utf-8'))
			elif base == "cover" and extension == ".jpg":
				# not in use now since we do not support cover yet
				found_cover = True 
				cover_data = zfile.open(fname).read()
			
			"""
			if (extension ==".json" or extension == ".mei" or extension == ".xml"
				or extension == '.mxl' or extension=='.krn' or extension=='.abc' or extension == '.musicxml'):
				valid_namelist.append(fname)
			else:
				print ("Ignoring file %s.%s" % (base, extension))

		for valid_name in valid_namelist:
			base, extension = decompose_zip_name(valid_name)
			cur_file = zfile.read(valid_name)
			m21_score, musicdoc = load_score(index_name, cur_file, extension[1:], base)
			print("Successfully loaded and saved the score:", valid_name)
			m21scores[base] = m21_score
			musicdocs[base] = musicdoc

		return m21scores, musicdocs

def load_and_process_zip(index_name, byte_str):

		"""
		Check validity and get content by calling read_zip(), 
		which includes getting m21 streams and musicdoc objects saved in database by calling load_score().
		Then extract features and get MusicSummary,
		and finally index them in ES.
		"""
		try:
			m21scores, musicdocs = read_zip(index_name, byte_str)
		except Exception as ex:
			print ("Exception when trying to call load_zip()" + " Message:" + str(ex))

		# Process the current score, produce descriptors from MusicSummary
		for score_id in m21scores:
			try:
				# Get MusicSummary and extracted descriptors
				descr_dict, encodedMS = process_score(musicdocs[score_id], m21scores[score_id], score_id)

				# Index the current musicdoc, including id, musicsummary and its descriptors in "index_name" index
				index_wrapper = IndexWrapper(index_name) 
				index_wrapper.index_musicdoc(index_name, musicdocs[score_id], descr_dict, encodedMS)
				print("Successfully indexed the current document: ", score_id)
			except:
				print("Ignoring score", score_id, " since error occurred while processing")
				continue
		return

def load_score(index_name, score, s_format, docid):
		"""
			Load a music score and save in database
		"""
		if s_format != "mei" and s_format != "xml" and s_format != "krn" and s_format != "abc" and s_format != "musicxml": #and s_format != "mid": #need to work on midi
			print("Document format not supported for loading the current score.")
			return
		
		# The original score -> M21 score
		if s_format == "mei":
			conv = mei.MeiToM21Converter(score)
			m21_score = conv.run()
			musicdoc = save_data(index_name, docid, s_format, score, m21_score)
			return m21_score, musicdoc

		elif s_format == "xml" or s_format == "krn" or s_format == "musicxml" or s_format == "mid":
			m21_score = converter.parse(score)
			musicdoc = save_data(index_name, docid, s_format, score, m21_score)
			return m21_score, musicdoc

		elif s_format == "abc":
			handler = abcFormat.ABCHandler()
			handler.process(score)
			m21_score = m21.abcFormat.translate.abcToStreamScore(handler)
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
			# Feature extraction
			descr_dict = extract_features(score, MS, musicdoc)
			print(descr_dict)# for testing
		except Exception as ex:
			print("Error while extracting features from ", doc_id, ":",str(ex))

		return descr_dict, encodedMS
