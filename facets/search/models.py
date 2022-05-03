from django.db import models

# Create your models here.

class DummyPattern(models.Model):
    pattern = models.CharField(max_length=255)
    
    def __str__(self):
        return "--" + self.pattern + "--"
