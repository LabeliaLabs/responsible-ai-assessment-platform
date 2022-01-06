from django.db.models import JSONField
from django.db import models

from .assessment import Assessment


class EvaluationElementWeight(models.Model):
    """
    Weight that is given to each evaluation element when the score is calculated (pondération d'importance)
    This class defines for a type of organization, a json field in which the keys are the evaluation elements
    of a given assessment and the values the weight attributed to each evaluation element.
    This weight will be applied to calculate the scoring by multiplying the number of points of an evaluation element
    by its weight
    This is useful when you want to emphasize an evaluation element for an orga type or an overall section
    """

    name = models.CharField(max_length=500)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    organisation_type = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        default="entreprise"
    )
    # todo change organisation_type field
    master_evaluation_element_weight_json = JSONField()

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Evaluation elements weight (id {str(self.pk)})"

    def get_master_element_weight(self, master_element):
        """
        Get the master element weight registered for the object in the
        json field master_evaluation_element_weight_json
        :param master_element: a master choice of the assessment
        :return: float
        """
        if master_element.master_section.assessment == self.assessment:
            return float(
                self.master_evaluation_element_weight_json[master_element.get_numbering()]
            )
        else:
            # SET ERROR
            print(
                "Erreur, le master element n'appartient pas au même assessment que le scoring"
            )
            return None
