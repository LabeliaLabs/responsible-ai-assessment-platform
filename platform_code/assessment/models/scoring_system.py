from django.db.models import JSONField
from django.db import models

from .assessment import Assessment


class ScoringSystem(models.Model):
    """
    The ScoringSystem class is used to define, for an assessment, the weight of each of its master_choices
    This information is stored in a json filed, where keys are master_choice ids and values are the weight
    (float numbers)
    This class is useful to set the gap between the choices inside an evaluation element
    """

    name = models.CharField(max_length=500)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    version = models.CharField(max_length=255, blank=True, null=True)
    organisation_type = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        default="entreprise"
    )  # todo change this field
    master_choices_weight_json = JSONField()
    # this coefficient is used to split the points for elements not applicable
    attributed_points_coefficient = models.FloatField(default=0.5)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Scoring system (id {str(self.pk)})"

    def get_master_choice_points(self, master_choice):
        """
        Get the float number in the master_choices_weight_json
        which is associated to the points of the master choice
        :param master_choice: a master choice of
        :return: float
        """
        if (
                master_choice.master_evaluation_element.master_section.assessment
                == self.assessment
        ):
            try:
                choice_points = float(
                    self.master_choices_weight_json[str(master_choice.get_numbering())]
                )
                return choice_points
            except KeyError as e:
                # todo logs
                print(
                    "Le choix n'est pas dans le dictionnaire du scoring, erreur {0}".format(
                        e
                    )
                )
        else:
            print(
                "Erreur, le master choice n'appartient pas au même assessment que le scoring"
            )
