from django.db import models

from datetime import datetime
import json

from pathlib import Path
from django.core.files import File

from django.urls import reverse

from .utils import OverwriteStorage

class Index(models.Model):
	name = models.CharField(max_length=255, unique = True)
	#description = models.CharField(max_length=255, unique = True)

	def __str__(self):
		return self.name

class Person(models.Model):
	'''Persons (authors, composers, etc)'''

	name = models.CharField(max_length=100, unique = True)
	country = models.CharField(max_length=100)
	year_birth = models.IntegerField(null = True, blank = True)
	year_death = models.IntegerField(null = True, blank = True)
	wikidata_url = models.CharField(max_length=255, null=True)

	class Meta:
		db_table = "Person"	

	def __str__(self):
		return self.name

class MusicDoc(models.Model):
	'''
	Save the music file and its index, id, type in database
	'''
	
	index = models.ForeignKey(Index, on_delete=models.CASCADE)
	doc_id = models.CharField(max_length=255, unique=True)
	doc_type = models.CharField(max_length=255, null=True, blank=True)
	
	def upload_path(self, filename):
		# File will be uploaded to MEDIA_ROOT/<doc_id>/<filename>
		return '%s/%s' % (self.doc_id, filename)
	
	"""
	def load_score(self):
		score = Score()
 		if self.doc_type == 'krn':
            doc = self.krnfile
            # To add: loading module in Score.py
        elif self.doc_type == 'musicxml':
            doc = self.musicxmlfile
            # To add: loading module in Score.py
        elif self.doc_type == 'mei':
			score.load_from_xml(self.meifile.path, "mei")
			return score
        elif self.doc_type == 'xml':
			score.load_from_xml(self.musicxmlfile.path, "musicxml")
			return score
        elif self.doc_type == 'abc':
        	doc = self.abcfile
        	# To add: loading module in Score.py
		else:
			raise LookupError ("MusicDoc " + self.doc_id + " doesn't have any file attached")
    """


	musicxmlfile = models.FileField(upload_to=upload_path, null=True, blank=True, storage=OverwriteStorage())
	xmlfile = models.FileField(upload_to=upload_path, null=True, blank=True, storage=OverwriteStorage())
	krnfile = models.FileField(upload_to=upload_path, null=True, blank=True, storage=OverwriteStorage())
	meifile = models.FileField(upload_to=upload_path, null=True, blank=True, storage=OverwriteStorage())
	abcfile = models.FileField(upload_to=upload_path, null=True, blank=True, storage=OverwriteStorage())

	m21score = models.TextField(null=True, blank=True)

	# Metadata:
	title = models.CharField(max_length=255, null=True, blank=True)
	composer = models.ForeignKey(Person, null=True, blank=True, on_delete=models.CASCADE)
	#multiple composers???

	def add_info(self, mkey, mvalue):
		"""
		Given a key as the name of the info,
		and given a value as the value of this featur.
		"""

		# The key must belongs to the pre-defined list
		if mkey not in Metainfo.META_KEYS:
			raise Exception(f"Sorry, the key {mkey} does not belong to the list")
		
		try:
			meta_pair = Metainfo.objects.get(doc=self, meta_key=mkey)
		except Metainfo.DoesNotExist as e:
			meta_pair = Metainfo(doc=self, meta_key=mkey, meta_value=mvalue)
			meta_pair.save()

	def get_info(self):
		"""Return the list of key-value pairs"""
		metas = []
		for m in Metainfo.objects.filter(doc=self):
			m.label = Metainfo.META_KEYS[m.meta_key]["label"]
			metas.append(m)
		return metas

	def __str__(self):
		return self.doc_id

class Descriptor(models.Model):
	'''
	A descriptor is a textual representation for some musical feature, used for full text indexing
	'''
	
	doc = models.ForeignKey(MusicDoc, on_delete=models.CASCADE)
	part = models.CharField(max_length=30)
	voice = models.CharField(max_length=30)
	descr_type = models.CharField(max_length=30)
	value = models.TextField()

	def to_dict(self):
		return dict(voice=self.voice, value=self.value)


class Metainfo(models.Model):

	doc = models.ForeignKey(MusicDoc, on_delete=models.CASCADE)
	meta_key = models.CharField(max_length=255)
	meta_value = models.TextField()

	# List of allowed meta keys, 
	MK_MODE = "mode" # should we delete this? there's key mode
	MK_GENRE = "genre" 
	MK_COMPOSER = "composer" # should we delete? there's Person model
	MK_KEY_TONIC = "key_tonic_name"
	MK_KEY_MODE = "key_mode"
	MK_NUM_OF_PARTS = "num_of_parts"
	MK_NUM_OF_MEASURES = "num_of_measures"
	MK_NUM_OF_NOTES = "num_of_notes"
	ML_INSTRUMENTS = "instruments"
	MK_LOWEST_PITCH_EACH_PART = "lowest_pitch_each_part"
	MK_HIGHEST_PITCH_EACH_PART = "highest_pitch_each_part"
	MK_MOST_COMMON_PITCHES = "most_common_pitches"
	MK_AVE_MELODIC_INTERVAL = "average_melodic_interval"
	MK_DIRECTION_OF_MOTION = "direction_of_motion"
	MK_MOST_COMMON_NOTE_QUARTER_LENGTH = "most_common_note_quarter_length"
	MK_RANGE_NOTE_QUARTER_LENGTH = "range_note_quarter_length"
	MK_INIT_TIME_SIG = "initial_time_signature"

	# Descriptive infos for meta pairs
	META_KEYS = {
		MK_MODE: {"label": "Mode"},
		MK_GENRE: {"label": "Genre"},
		MK_COMPOSER: {"label": "Composer"},
		MK_KEY_TONIC: {"label": "Key Tonic Name"},
		MK_KEY_MODE: {"label":"Key Mode"},
		MK_NUM_OF_PARTS: {"label": "Number of parts"},
		MK_NUM_OF_MEASURES: {"label": "Number of measures"},
		MK_NUM_OF_NOTES: {"label": "Number of notes"},
		ML_INSTRUMENTS: {"label": "Instruments"},
		MK_LOWEST_PITCH_EACH_PART: {"label": "Lowest pitch each part"},
		MK_HIGHEST_PITCH_EACH_PART: {"label": "Highest pitch each part"},
		MK_MOST_COMMON_PITCHES: {"label": "Most common pitches"},
		MK_AVE_MELODIC_INTERVAL: {"label": "Average melodic interval"},
		MK_DIRECTION_OF_MOTION: {"label": "Direction of motion"},
		MK_MOST_COMMON_NOTE_QUARTER_LENGTH: {"label": "Most common note quarter length"},
		MK_RANGE_NOTE_QUARTER_LENGTH: {"label": "Range of note quarter length"},
		MK_INIT_TIME_SIG:{"label": "Initial time signature"}
	}
