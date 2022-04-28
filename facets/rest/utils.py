from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
             os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
