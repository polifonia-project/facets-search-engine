from django.db import models

from datetime import datetime
import json

class Index(models.Model):
	index_name = models.CharField(max_length=255)

	def __str__(self):
		return self.index_name

class MusicDoc(models.Model):
	index = models.ForeignKey(Index, on_delete=models.CASCADE)
	doc_id = models.CharField(max_length=255, unique=True)
	doc_type = models.CharField(max_length=255)
	#title = models.CharField(max_length=255, null=True, blank=True)
	#composer = models.CharField(max_length=255, null=True, blank=True)

	#musicxml = models.FileField(upload_to=upload_path,null=True,storage=OverwriteStorage())
	#mei = models.FileField(upload_to=upload_path,null=True,storage=OverwriteStorage(), max_length=255)

	def __str__(self):
		return self.doc_id
