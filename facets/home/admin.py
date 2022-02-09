from django.contrib import admin

from .models import Index
from .models import MusicDoc

admin.site.register(Index)
admin.site.register(MusicDoc)