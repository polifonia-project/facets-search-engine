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
from binascii import unhexlify

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


		except  Exception as ex:
			print ("Exception when trying to write descriptor" + music_summary.doc_id + " Message:" + str(ex))

		return descr_dict

def load_zip(byte_str):
		#zipfile should contain at least one music scores in the format recognized(mei, musicxml etc.)
		print(type(byte_str))
		#print("bytestr:", byte_str)
		strfile = open("teststr.txt", "wb")
		strfile.write(byte_str)
		strfile.close()

		zfile = zipfile.ZipFile(io.BytesIO(byte_str), "r")

		print("made it here!")
		for fname in zfile.namelist():
			# Skip files with weird names
			base, extension = decompose_zip_name(fname)
			if base == "" or base.startswith('_') or  base.startswith('.'):
				continue
			if (extension ==".json" or extension == ".mei" or extension == ".xml"
				or extension == '.mxl' or extension == '.krn' or extension == '.mid'):
				files[base] = {"mei": "", 
						"musicxml": "",
						"compressed_xml": "",
						"json": "",
						"kern": ""}
			else:
				print ("Ignoring file %s.%s" % (base, extension))

		for fname in zfile.namelist():
			ref, extension = decompose_zip_name(fname)
			if ref in files:
				if extension == '.mei':
					files[ref]["mei"] = load_score(fname, "mei")

		#save_zip_data(zfile)

		return files

def save_zip_data(zfile):
		#TODO, save the scores in database
		"""
		# This part for later when we allow multiple formats... for saving them in the database
		# Second scan: we note the files present for each opus
		for fname in zfile.namelist():
			(ref, extension) = decompose_zip_name(fname)
			if ref in files:
				if extension == '.mxl':
					files[ref]["compressed_xml"] = fname
				elif (extension == '.xml' or extension == '.musicxml'):
					files[ref]["musicxml"] = fname
				elif extension == '.mei':
					files[ref]["mei"] = fname
				elif extension == '.json':
					files[ref]["json"] = fname
				elif extension == '.mid':
					files[ref]["midi"] = fname
				elif extension == '.krn':
					files[ref]["kern"] = fname

		# Now in files, we know whether we have the MusicXML, MEI or any other file format
		list_imported = []
		for ref, files_desc in files.items():
				print ("Import music doc with doc_id " + ref)
				# Check if it already exists:
				try:
					musicdoc = MusicDoc.objects.get(doc_id=ref)
				except MusicDoc.DoesNotExist as e:
					musicdoc = MusicDoc(doc_id=ref)
				list_imported.append(musicdoc)

				#Not for now since we do not have metadata yet
				# If a json exists, then it should contain the relevant metadata
				if files_desc["json"] != "":
					logger.info ("Found JSON metadata file %s" % files_desc["json"])
					json_file = zfile.open(files_desc["json"])
					json_doc = json_file.read()
					musicdoc.load_from_dict (corpus, json.loads(json_doc.decode('utf-8')))
				musicdoc.save()

				#Not for now since we don't use format other than MEI yet...
				#Save the doc in database
				if files_desc["compressed_xml"] != "":
					logger.info ("Found compressed MusicXML content")
					# Compressed XML
					container = io.BytesIO(zfile.read(opus_files_desc["compressed_xml"]))
					xmlzip = zipfile.ZipFile(container)
					# Keep the file in the container with the same basename
					for name2 in xmlzip.namelist():
						basename2 = os.path.basename(name2)
						ref2 = os.path.splitext(basename2)[0]
						if files_desc["opus_ref"]  == ref2:
							xml_content = xmlzip.read(name2)
					musicdoc.musicxml.save("score.xml", ContentFile(xml_content))
				if files_desc["musicxml"] != "":
					logger.info ("Found MusicXML content")
					xml_content = zfile.read(files_desc["musicxml"])
					musicdoc.musicxml.save("score.xml", ContentFile(xml_content))
				if files_desc["kern"] != "":
					logger.info ("Found KERN content")
					kern_content = zfile.read(files_desc["kern"])
					# We need to write in a tmp file, probably 
					tmp_file = "/tmp/tmp_kern.txt"
					f = open(tmp_file, "w")
					lines = kern_content.splitlines()
					for line in lines:
						if not (line.startswith(b"!!!ARE: ") 
							or line.startswith(b"!!!AGN: ")
							or line.startswith(b"!!!OTL: ")
							or line.startswith(b"!!!YOR: ")
							or line.startswith(b"!!!SCA: ")
							or line.startswith(b"!!!OCY: ")
							or line.startswith(b"!! ")
							):
							f.write (line.decode()  + os.linesep)
					f.close()
					try:
						tk = verovio.toolkit()
						tk.loadFile(tmp_file)
						mei_content = tk.getMEI()
						musicdoc.mei.save("mei.xml", ContentFile(mei_content))
						doc = minidom.parseString(mei_content)
					except Exception as e:
						print ("Exception while loading Kern: " + str(e))
						return

				#For saving MEI file in database
				if bool(musicdoc.mei) == False:
					if files_desc["mei"] != "":
						logger.info ("Load MEI content")
						# Add the MEI file
						try:
							mei_file = zfile.open(files_desc["mei"])
							mei_raw  = mei_file.read()
							encoding = "utf-8"
							try:
								logger.info("Attempt to read in UTF 8")
								mei_raw.decode(encoding)
							except Exception as ex:
								logger.info("Read in UTF 16")
								encoding = "utf-16"
								mei_raw.decode(encoding)
							logger.info("Correct encoding: " + encoding)
							mei_content = mei_raw.decode(encoding)
							logger.info ("Save the MEI file in database.")
							musicdoc.mei.save("mei.xml", ContentFile(mei_content))
						except Exception as ex:
							logger.error ("Error processing MEI  " + str(ex))
					else:
						# Produce the MEI from the MusicXML
						if files_desc["musicxml"] != "":
							logger.info ("Produce the MEI from MusicXML")
							try:
								tk = verovio.toolkit()
								tk.loadFile(musicdoc.musicxml.path)
								mei_content = tk.getMEI()
								musicdoc.mei.save("mei.xml", ContentFile(mei_content))
							except Exception as e:
								print ("Exception : " + str(e))
						else:
							logger.warning ("No MEI, no MusicXML: content %s is incomplete" % musicdoc.doc_id)
		"""
		return

def load_score(score, s_format):

		if s_format == "mei":
			conv = mei.MeiToM21Converter(score)
			# Get M21 object of the score
			m21_score = conv.run()
			return m21_score
		elif s_format == "xml" or s_format == "krn" or s_format == 'mid' or s_format == "musicxml":
			m21_score = converter.parse(score)
			return m21_score
		elif s_format == "abc":
			print(score)
			handler = abcFormat.ABCHandler()
			handler.process(score)
			m21_score = m21.abcFormat.translate.abcToStreamScore(handler)
			return m21_score

		
def score_process(m21_score, doc_id):

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
	 	
	 	# Create a musicdoc object
		musicdoc = MusicDoc()
		musicdoc.doc_id = doc_id
		# TO- DO: SAVE METADATA AND SCORE(Original file? music21? both?) IN DATABASE

		try:
			# Feature extraction
			descr_dict = extract_features(score, MS, musicdoc)
		except Exception as ex:
			print("Error while extracting features", str(ex))

		return musicdoc, descr_dict, encodedMS
