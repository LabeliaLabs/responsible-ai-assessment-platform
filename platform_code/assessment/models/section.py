import random

from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse

from .assessment import Assessment


class MasterSection(models.Model):
    """
    This class stores static data concerning the sections of the assessment
    """

    name = models.CharField(max_length=200)
    # This class is a sub part of the class assessment, may be we need to check the on_delete
    assessment = models.ForeignKey(Assessment, blank=True, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    order_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_id"]

    def __str__(self):
        if self.order_id and self.name:
            return f"Master section S{str(self.order_id)} {self.name}"
        elif self.order_id and not self.name:
            return f"Master section S{str(self.order_id)}"
        else:
            return f"Master section (id {str(self.pk)})"

    def get_numbering(self):
        """
        Return the number of the master section (string)
        :return:
        """
        if self.order_id:
            return str(self.order_id)


class Section(models.Model):
    """
    A section is a part of an evaluation and is defined by a master_section from which static data
    can be obtained (name, evaluation)
    """

    master_section = models.ForeignKey(MasterSection, on_delete=models.CASCADE)
    evaluation = models.ForeignKey("assessment.Evaluation", blank=True, on_delete=models.CASCADE)
    user_progression = models.IntegerField(
        default=0
    )  # progression of user inside this section, as percentage
    points = models.FloatField(default=0)
    max_points = models.FloatField(default=0, blank=True, null=True)
    # This field "fetch" is used for the versioning of assessments
    fetch = models.BooleanField(default=True)
    user_notes = models.TextField(blank=True, null=True, max_length=20000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.master_section.order_id:
            return (
                    "S" + str(self.master_section.order_id) + " " + self.master_section.name
            )
        else:
            return self.master_section.name

    @classmethod
    def create_section(cls, master_section, evaluation):
        section = cls(master_section=master_section, evaluation=evaluation)
        section.save()
        return section

    def get_absolute_url(self):
        return reverse(
            "assessment:section",
            kwargs={
                "orga_id": self.evaluation.organisation.id,
                "slug": self.evaluation.slug,
                "pk": self.evaluation.pk,
                "id": self.id,
                "name": slugify(self.master_section.keyword),
                "page": self.master_section.order_id,
            },
        )

    def fill_notes(self):
        """
        Fill the notes with random string
        """
        words = ["les moutons", "sont", "bien", "gardés", "dans la bergerie"]
        random.shuffle(words)
        self.user_notes = ' '.join(words)
        self.save()

    def set_progression(self):
        """
        Update the status of the section which is a float number calculated by dividing
        the number of evaluation_element treated by the global number of evaluation_element
        """

        evaluation_element_list = self.evaluationelement_set.all()
        count_element_done = 0
        # If not empty
        if list(evaluation_element_list):
            for element in evaluation_element_list:
                if (
                        element.status or not element.is_applicable()
                ):  # the element has been answered or is not applicable
                    count_element_done += 1
            self.user_progression = int(
                round(count_element_done * 100 / len(evaluation_element_list), 0)
            )
        self.save()

    def set_points(self):
        """ Set the points for a section according to the points set by each evaluation element of the section"""
        sum_points = 0
        for element in self.evaluationelement_set.all():
            # We only count the points of applicable element, the other points will be affected when
            # the evaluation score will be calculated
            if element.is_applicable():
                sum_points += element.points
        self.points = sum_points
        self.save()

    def set_max_points(self):
        """
        Calculate the max possible points for a section
        """
        max_points = 0
        for element in self.evaluationelement_set.all():
            max_points += element.max_points
        self.max_points = max_points
        self.save()

    def get_points_not_concerned(self):
        """
        Get the sum of the points not concerned within a section, due to conditions inter evaluation elements or
        to conditions intra evaluation elements.
        """
        evaluation_score = self.evaluation.evaluationscore_set.first()
        evaluation_element_weight = evaluation_score.get_element_weight()
        sum_points_not_concerned = 0
        for element in self.evaluationelement_set.all():
            # Check this is useful to calculate points not concerned (condition intra or inter)
            if element.has_condition_between_choices() or not element.is_applicable():
                element_weight = evaluation_element_weight.get_master_element_weight(
                    element.master_evaluation_element
                )
                sum_points_not_concerned += element.calculate_points_not_concerned() * element_weight
        return sum_points_not_concerned

    def calculate_score_per_section(self):
        """
        Apply the compensation in case there are points not concerned.
        Multiply the dilatation factor with the points obtained and sum it with half the points not
        concerned.
        """
        pts_not_concerned = self.get_points_not_concerned()
        coeff = self.evaluation.evaluationscore_set.first().coefficient_scoring_system
        dilatation_factor = (self.max_points - pts_not_concerned * coeff) / (self.max_points - pts_not_concerned)
        return self.points * dilatation_factor + coeff * pts_not_concerned
