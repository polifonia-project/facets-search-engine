"""
	Processing scores or zip of scores.

	Transform score to music21 stream to MusicSummary,
	get metadata, extract features.

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
import xml.etree.ElementTree as ET
import re

def get_metadata_from_score(doctype, score, m21_score):
	
	#TODO: clean the '\n's from composer names and title names. kern
	# TODO2: multiple composers by Music21
	metainfo = {"title":"", "composer":""}
	
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
		if m21_score.metadata.composer != None and m21_score.metadata.composer != "":
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
		print("Title of this musicdoc: ", metainfo["title"])
	else:
		print("Couldn't find title information of this musicdoc.")
	if metainfo["composer"] != "":
		print("Composer of this musicdoc: ", metainfo["composer"])
	else:
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
		try:
			metainfo = get_metadata_from_score(doctype, score, m21_score)
		except:
			# in case there is an error, just skip and leave these fields empty
			metainfo = {"title":"", "composer":""}

		if metainfo["title"] != '':
			musicdoc.title = metainfo["title"]
		if metainfo["composer"] != '':
			musicdoc.composer = metainfo["composer"]

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

	info["num_of_parts"] = len(m21_score.getElementsByClass(stream.Part))
	#info["num_of_voices"] = len(m21_score.getElementsByClass(stream.Voice))
	info["num_of_measures"] = 0
	for part in m21_score.parts:
		info["num_of_measures"] += len(part)

	info["num_of_notes"] = len(m21_score.flatten().getElementsByClass(note.Note))

	info["instruments"] = []
	if instrument.partitionByInstrument(m21_score) != None:
		for part in instrument.partitionByInstrument(m21_score):
			info["instruments"].append(part.getInstrument())
			# TODO: from music21 object to string
	
	print("Info of the score:", info)

	print("Pitch analysis:")
	nameCount = analysis.pitchAnalysis.pitchAttributeCount(m21_score, 'name')
	print("10 most common pitch and occurrence:")
	for n, count in nameCount.most_common(10):
		print("%2s: %2d" % (n, nameCount[n]))

	"""
	pcCount = analysis.pitchAnalysis.pitchAttributeCount(m21_score, 'pitchClass')
	# can use nameWithOctave or name
	for n in sorted(pcCount):
		print("%2d notes in pitch class%2d" % (pcCount[n] , n))
	"""
	p = analysis.discrete.Ambitus()
	count = 0
	for part in m21_score.parts:
		count += 1
		pitchMin, pitchMax = p.getPitchSpan(part)
		# Could be used to analyse each measure
		print("Lowest pitch of part", count, "is ", pitchMin)
		print("Highest pitch of part", count, "is ", pitchMax)
	
	# pitch histogram?
	#fe = features.jSymbolic.BasicPitchHistogramFeature(m21_score)

	fe = features.jSymbolic.AverageMelodicIntervalFeature(m21_score)
	print("Average melodic interval in semitones:", fe.extract().vector)

	fe = features.jSymbolic.DirectionOfMotionFeature(m21_score)
	print("Direction of motion (the fraction of melodic intervals that are rising rather than falling):", fe.extract().vector[0])

	print("\nNote length analysis:")

	fe = features.native.MostCommonNoteQuarterLength(m21_score)
	print("Most common note quarter length:", fe.extract().vector[0])

	fe = features.native.RangeOfNoteQuarterLengths(m21_score)
	print("Difference between the longest and shortest quarter lengths:", fe.extract().vector[0])

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
	print("\nInitial time signature:", fe.extract().vector)

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

		# TODO: work with json metadata
		found_metadata = False
		meta_dict = {}

		for fname in zfile.namelist():
			# Skip files with weird names
			base, extension = decompose_zip_name(fname)

			# base is file name, will be used as doc_id, extension is the file format
			if base == "" or base.startswith('_') or base.startswith('.'):
				continue

			# TODO: if there is a folder within zip, work with it

			# Read json of the corpus data
			if extension == ".json":
				# should check name of the json file to know if it is for a single score or the whole zip...
				found_metadata = True
				#meta_dict = json.loads(zfile.open(fname).read().decode('utf-8'))
				meta_dict = json.loads(zfile.read(fname).decode('utf'))
				#THIS meta_dict SHOULD BE USED LATER IN SAVE_DATA but is there a better way?
				#metainfo_zip = load_meta_from_json(meta_dict)
			

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

		return m21scores, musicdocs

def load_and_process_zip(index_name, byte_str):

		"""
		Check validity and get content by calling read_zip(), 
		which includes getting m21 streams and musicdoc objects saved in database by calling load_score().
		Then extract features and get MusicSummary,
		and finally index them in ES.
		"""
		m21scores = {}
		musicdocs = {}

		try:
			m21scores, musicdocs = read_zip(index_name, byte_str)
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
					descr_dict, encodedMS = process_score(musicdocs[score_id], m21scores[score_id], score_id)

					# Index the current musicdoc, including id, musicsummary and its descriptors in "index_name" index
					index_wrapper = IndexWrapper(index_name) 
					index_wrapper.index_musicdoc(index_name, musicdocs[score_id], descr_dict, encodedMS)
					print("Successfully indexed the current document: ", score_id)
				except:
					print("Ignoring score", score_id, ", error occurred while processing")
					continue
			return False

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
			# Feature extraction
			descr_dict = extract_features(score, MS, musicdoc)
		except Exception as ex:
			print("Error while extracting features from ", doc_id, ":",str(ex))

		return descr_dict, encodedMS
