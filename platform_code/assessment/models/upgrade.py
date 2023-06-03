from django.db import models
from django.db.models import JSONField

from .assessment import Assessment


class Upgrade(models.Model):
    """
    This class aims to contain the modifications of the assessment between each versions
    You can refer to the file "multiple_version.md" in the spec for more information
    """

    final_assessment = models.ForeignKey(
        Assessment, related_name="final_assessment", on_delete=models.CASCADE
    )
    origin_assessment = models.ForeignKey(
        Assessment, related_name="origin_assessment", on_delete=models.CASCADE
    )
    upgrade_json = JSONField()

    def __str__(self):
        return (
            "Upgrade from V"
            + str(self.origin_assessment.version)
            + " to V"
            + str(self.final_assessment.version)
        )
