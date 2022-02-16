# ScoreProcessing.py

# Transform a Music21 object into MusicSummary 
# Then extract features from MS.

from lib.music.Score import *
from lib.music.MusicSummary import *
from rest.models import *

def extract_features(MS):

		'''
		Extract features
		'''
		return

def score_process(m21_score, index_name, doc_id):

		score = Score()
	
		# Get a Score object from M21 object of the score. 
		score.load_component(m21_score)
	 	
	 	#Create object musicdoc, save metadata

		musicdoc = MusicDoc()
		musicdoc.doc_id = doc_id

		# Get MusicSummary from the Score object

		MS = score.get_music_summary()

		extract_features(MS)

		return musicdoc
