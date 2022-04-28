from django.db import models

from datetime import datetime
import json

from pathlib import Path
from django.core.files import File

from .utils import OverwriteStorage

class Index(models.Model):
	name = models.CharField(max_length=255)

	def __str__(self):
		return self.index_name

class MusicDoc(models.Model):
	'''
	Save the music document and its index, id, type in database
	'''
	#def upload_path(self, filename):
	#	'''Set the path where files must be stored'''
	#	return 'musicdoc/%s' % (self.doc_id, "/")

	index = models.ForeignKey(Index, on_delete=models.CASCADE)
	doc_id = models.CharField(max_length=255, unique=True)
	doc_type = models.CharField(max_length=255, null=True, blank=True)


	def upload_path(self, filename):
		# file will be uploaded to MEDIA_ROOT/<doc_id>/<filename> FOR NOW
		return '{0}/{1}'.format(self.doc_id, filename)

	#musicfile = models.FileField(upload_to=upload_path, null=True, blank=True, storage=OverwriteStorage())
	# is max_length a problem for m21score?
	m21score = models.CharField(max_length=255, null=True, blank=True)

	#title = models.CharField(max_length=255, null=True, blank=True)
	#composer = models.CharField(max_length=255, null=True, blank=True)

	def __str__(self):
		return self.doc_id

class Descriptor(models.Model):
	'''
	A descriptor is a textual representation for some musical feature, used for full text indexing
	'''
	doc = models.ForeignKey(MusicDoc,on_delete=models.CASCADE)
	part = models.CharField(max_length=30)
	voice = models.CharField(max_length=30)
	descr_type = models.CharField(max_length=30)
	value = models.TextField()

	def to_dict(self):
		return dict(part=self.part, voice=self.voice, value=self.value)
