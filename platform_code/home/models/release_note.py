from django.db import models


class ReleaseNote(models.Model):
    """
    Release Notes are used in the release-notes.html page by release_notes.py
    """
    date = models.DateField()
    text = models.TextField(null=False, blank=False)
    version = models.CharField(max_length=150)
