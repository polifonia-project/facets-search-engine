"""
	Transform a Music21 object into MusicSummary,
	Then extract features from MS.
"""

from lib.music.Score import *
from lib.music.MusicSummary import *
from rest.models import *

from music21 import converter, mei
import zipfile
import json
import io
import os
from binascii import unhexlify
#from django.core.files.base import ContentFile
from django.core.files import File

def save_data(index_name, m21_score, doc_id):

		# TO-DO: SAVE METADATA AND SCORE(Original file? music21? both?) IN DATABASE

		try:
			index = Index.objects.get(name = index_name)
		except:
			index = Index()
			index.name = index_name
			index.save()

		# If it already exists, delete
		MusicDoc.objects.filter(doc_id=doc_id).delete()

	 	# Create a musicdoc object
		musicdoc = MusicDoc()
		musicdoc.doc_id = doc_id
		musicdoc.index = index
		musicdoc.m21score = m21_score

		# To do: save the original score file
		# musicdoc.musicfile = score
		# To do 2: also save metadata
		#musicdoc.doc_type = 
		#musicdoc.save()

		return musicdoc

def extract_features(score, music_summary, musicdoc):

		descr_dict = {}
		try:
				types = "chromatic", "diatonic", "rhythmic", "lyrics", "notes"
				for atype in types:
					descr_dict[atype] = {}

				# Clean the current descriptors (TO-DO)
				##Descriptor.objects.filter(doc_id=musicdoc.doc_id).delete()
				
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
			print ("Exception when trying to write descriptor" + music_summary.doc_id + " Message:" + str(ex))

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

def load_zip(byte_str):
		#zipfile should contain at least one music scores in the format recognized(mei, musicxml etc.)
		
		#strfile for testing
		strfile = open("teststr.txt", "wb")
		strfile.write(byte_str)
		strfile.close()

		b = io.BytesIO(byte_str)

		zfile = zipfile.ZipFile(b, "r")

		valid_namelist = []
		m21scores = {}
		"""
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
			# Codes of import zip are migrated from neuma/manager/models.py
			"""
			if (extension ==".json" or extension == ".mei" or extension == ".xml"
				or extension == '.mxl' or extension=='.krn' or extension=='.abc' or extension == '.musicxml'):
				"""
				files[base] = {"mei": "", 
						"musicxml": "",
						"xml": "",
						"json": "",
						"kern": "",
						"abc": ""}
				"""
				valid_namelist.append(fname)
			else:
				print ("Ignoring file %s.%s" % (base, extension))

		for valid_name in valid_namelist:
			base, extension = decompose_zip_name(valid_name)
			cur_file = zfile.read(valid_name)
			m21_score = load_score(cur_file, extension[1:], base)
			print("Successfully loaded the score:", valid_name)
			m21scores[base] = m21_score

		return m21scores

def load_score(score, s_format, docid):
		"""
		Load a music score
		"""
		if s_format != "mei" and s_format != "xml" and s_format != "krn" and s_format != "abc": #and and s_format != "mid" and s_format != "musicxml":
			print("Document format not supported for loading the current score.")
			return
		
		if s_format == "mei":
			conv = mei.MeiToM21Converter(score)
			# Get M21 object of the score
			m21_score = conv.run()
			return m21_score

		elif s_format == "xml" or s_format == "krn":# or s_format == 'mid' or s_format == "musicxml":
			m21_score = converter.parse(score)
			return m21_score

		elif s_format == "abc":
			print(score)
			handler = abcFormat.ABCHandler()
			handler.process(score)
			m21_score = m21.abcFormat.translate.abcToStreamScore(handler)
			return m21_score
		
def score_process(index_name, m21_score, doc_id):
		"""
		From original score file to Score object, to MS object then extract features
		return musicdoc object, extracted features and MS, for indexing
		"""

		try:
			# Create a Score object
			score = Score()
			# Get a Score object from M21 object of the score. 
			score.load_component(m21_score)
		except Exception as ex:
			print("Error while loading the score using music21", str(ex))
	 	
		try:
	 		# Get MusicSummary from the Score object
			MS = score.get_music_summary()
			MS.doc_id = doc_id
			encodedMS = MS.encode()
		except Exception as ex:
			print("Error while encoding the score", str(ex))

		musicdoc = save_data(index_name, m21_score, doc_id)

		try:
			# Feature extraction
			descr_dict = extract_features(score, MS, musicdoc)
		except Exception as ex:
			print("Error while extracting features", str(ex))

		return musicdoc, descr_dict, encodedMS
