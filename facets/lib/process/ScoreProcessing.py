# ScoreProcessing.py

# Transform a Music21 object into MusicSummary 
# Then extract features from MS.

from lib.music.Score import *
from lib.music.MusicSummary import *

def score_process(m21_score):

	score = Score()
	
	# Get a Score object from M21 object of the score
	score.load_component(m21_score)
	 
	# Get MusicSummary from the Score object
	MusicSummary = score.get_musicsummary()

	return MusicSummary



