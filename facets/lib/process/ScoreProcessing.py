"""
	Transform a Music21 object into MusicSummary,
	Then extract features from MS.
"""

from lib.music.Score import *
from lib.music.MusicSummary import *
from rest.models import *

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
					# "this_voice" is a Voice object
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

def score_process(m21_score, index_name, doc_id):

		# Create a Score object
		score = Score()
		# Get a Score object from M21 object of the score. 
		score.load_component(m21_score)
	 	
	 	# Create a musicdoc object, to save metadata
		musicdoc = MusicDoc()
		musicdoc.doc_id = doc_id

		# Get MusicSummary from the Score object
		MS = score.get_music_summary()
		MS.doc_id = doc_id

		# Feature extraction
		descr_dict = extract_features(score, MS, musicdoc)

		return musicdoc, descr_dict
