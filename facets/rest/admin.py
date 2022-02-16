from django.contrib import admin

from .models import Index
from .models import MusicDoc
from .models import Descriptor

admin.site.register(Index)
admin.site.register(MusicDoc)
admin.site.register(Descriptor)