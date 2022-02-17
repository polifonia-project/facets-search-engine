# ScoreProcessing.py

# Transform a Music21 object into MusicSummary 
# Then extract features from MS.

from lib.music.Score import *
from lib.music.MusicSummary import *
from rest.models import *

def produce_descriptors(music_summary, musicdoc):

		descr_dict = {}
		try:
				types = "chromatic", "diatonic", "rhythmic", "notes"
				for atype in types:
					descr_dict[atype] = {}

				# Clean the current descriptors TODO
				##Descriptor.objects.filter(opus=opus).delete()
		
				for part_id, part in music_summary.parts.items():
					for voice_id, voice in part.items():
						# Melody descriptor
						music_descr = voice.get_chromatic_encoding()

						descriptor = Descriptor()
						descriptor.doc = musicdoc
						descriptor.part = part_id
						descriptor.voice = voice_id
						descriptor.descr_type = "chromatic"
						descriptor.value = music_descr

						descr_dict["chromatic"][str(voice_id)] = descriptor.to_dict()

		except  Exception as ex:
			print ("Exception when trying to write descriptor" + music_summary.doc_id + " Message:" + str(ex))

		return descr_dict

def score_process(m21_score, index_name, doc_id):

		score = Score()
	
		# Get a Score object from M21 object of the score. 
		score.load_component(m21_score)
	 	
	 	# Create object musicdoc, save metadata
		musicdoc = MusicDoc()
		musicdoc.doc_id = doc_id

		# Get MusicSummary from the Score object
		MS = score.get_music_summary()
		MS.doc_id = doc_id

		# Feature extraction
		descr_dict = produce_descriptors(MS, musicdoc)

		return musicdoc, descr_dict
