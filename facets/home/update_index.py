"""
Update the info on a selected index upon request
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

