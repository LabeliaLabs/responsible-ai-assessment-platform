from django.db import models

from .assessment import Assessment


class ElementChangeLog(models.Model):
    """
    This class is used to manage the change logs for evaluation elements, where edito are used to store
    information about evaluation elements of a specific version with regards to a previous one
    """

    edito = models.TextField(null=True, blank=True)
    pastille = models.CharField(max_length=200, null=False)
    eval_element_numbering = models.CharField(max_length=200, null=False)

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="new_assessment"
    )
    previous_assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="old_assessment", null=True
    )
    visibility = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def hide(self):
        self.visibility = False
        self.save()

    def display(self):
        self.visibility = True
        self.save()

    @classmethod
    def create_element_change_log(
        cls,
        edito_en,
        edito_fr,
        pastille_en,
        pastille_fr,
        eval_element_numbering,
        previous_assessment,
        new_assessment,
    ):
        change_log = cls(
            edito_en=edito_en,
            edito_fr=edito_fr,
            pastille_en=pastille_en,
            pastille_fr=pastille_fr,
            eval_element_numbering=eval_element_numbering,
            previous_assessment=previous_assessment,
            assessment=new_assessment,
        )

        change_log.save()
