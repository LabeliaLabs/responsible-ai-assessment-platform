from django.db import models


class Footer(models.Model):
    logo = models.ImageField(upload_to='logo')
    link = models.URLField()
    name = models.CharField(max_length=255)
