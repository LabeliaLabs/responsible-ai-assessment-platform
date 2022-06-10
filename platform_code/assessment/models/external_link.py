from django.db import models


class ExternalLink(models.Model):
    # Todo rename as Resources
    """
    This class manages the resources of the assessment. A resource is just a text which will be markdownify when it
    will be displayed.

    """
    # Name of the resource, will be displayed to the user
    text = models.TextField(max_length=4000, blank=True)
    type = models.CharField(default="Web article", max_length=500)

    def __str__(self):
        if self.text and self.type:
            return f"{self.text} ({self.type})"
        else:
            return f"Resource (id {str(self.pk)})"
