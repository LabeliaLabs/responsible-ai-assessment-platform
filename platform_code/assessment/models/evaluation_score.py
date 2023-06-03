from django.db import models
from django.db.models import JSONField

from .evaluation_element_weight import EvaluationElementWeight
from .scoring_system import ScoringSystem


class EvaluationScore(models.Model):
    """
    This class is used to store the evaluation scoring data

    need_to_set_max_points is a boolean field used to trigger or not the calculation the max points
    of the evaluation (so section and EE too).
    This field is used when the scoring is modified while the evaluation is already created.
    By default, set to False as the max points is set when the evaluation is created so no need to change it.

    need_to_calculate is a boolean field used to trigger or not the calculation of the different fields used to
    calculate the score (points obtained, dilatation factor, etc), in the method process_score_calculation.
    This is done only when the evaluation is finished.
    By default, this field is set to True as the score need to be calculated at least once. When the score is set,
    the value switches to False.
    When a modification is done while evaluation is finished, the value is set to True and the score will require to
    be calculated again.
    """

    evaluation = models.ForeignKey(
        "assessment.Evaluation", on_delete=models.CASCADE
    )  # TODO set OneToOne field
    # Boolean field to know if all the fields need to be calculated
    # if there are modifications after the 1st validation for example, the field switch from False to true
    need_to_set_max_points = models.BooleanField(default=False)
    need_to_calculate = models.BooleanField(default=True)

    # Static fields, do not depend on the evaluation choices
    max_points = models.FloatField(default=0, blank=True, null=True)
    coefficient_scoring_system = models.FloatField(default=0, blank=True, null=True)

    # Dynamic fields, depend on the evaluation choices
    points_not_concerned = models.FloatField(default=0, blank=True, null=True)
    points_obtained = models.FloatField(default=0, blank=True, null=True)
    points_to_dilate = models.FloatField(default=0, blank=True, null=True)
    dilatation_factor = models.FloatField(default=0, blank=True, null=True)

    # Json field with evaluation elements as keys and user exposition as value (boolean, True if concerned)
    exposition_dic = JSONField(default=dict)

    score = models.FloatField(default=0, blank=True, null=True)

    def __str__(self):
        return "Scoring data for the evaluation " + str(self.evaluation.id)

    @classmethod
    def create_evaluation_score(cls, evaluation):
        evaluation_score = cls(evaluation=evaluation)
        evaluation_score.save()
        evaluation_score.set_max_points()
        evaluation_score.coefficient_scoring_system = (
            evaluation_score.set_coefficient_scoring_system()
        )
        return evaluation_score

    def get_element_weight(self):
        """
        This method is used to get the element_weight object associated to the evaluation (and the assessment)
        :return:
        """
        # todo set the logic of organisation type
        organisation_type = "entreprise"
        # todo manage cases there are multiple objects
        evaluation_element_weight = EvaluationElementWeight.objects.filter(
            assessment=self.evaluation.assessment, organisation_type=organisation_type
        )[0]
        return evaluation_element_weight

    def set_coefficient_scoring_system(self):
        # TODO work on the organisation_type and see how to define it
        # organisation_type = self.section.evaluation.orga_id.type_orga  # Not implemented yet
        organisation_type = "entreprise"
        query_scoring_system = ScoringSystem.objects.filter(
            assessment=self.evaluation.assessment, organisation_type=organisation_type
        )
        if len(list(query_scoring_system)) == 1:
            self.coefficient_scoring_system = query_scoring_system[
                0
            ].attributed_points_coefficient
        else:
            # Todo see how we should manage communication with this case
            self.coefficient_scoring_system = 0.5
        self.save()

    def set_max_points(self):
        """
        Calculate the max points possible, used to calculate the score of an evaluation

        :return:
        """

        max_points = 0
        for section in self.evaluation.section_set.all():
            max_points += section.max_points
        self.max_points = max_points
        self.save()

    def calculate_max_points(self):
        """
        This method is used to set the max points of the whole evaluation (sections, EE)
        This is used after the scoring has been modified by a staff of the platform

        As the evaluation can be blank, in progress or finished, the points for each evaluation element already
        done need to be calculated again
        :return:
        """
        if self.need_to_set_max_points:
            max_points = 0
            for section in self.evaluation.section_set.all():
                for evaluation_element in section.evaluationelement_set.all():
                    evaluation_element.set_max_points()
                    # If the evaluation element is already answered, need to calculate again the points
                    if evaluation_element.status:
                        evaluation_element.set_points()
                section.set_max_points()
                max_points += section.max_points
                section.set_points()
            self.max_points = max_points
            self.need_to_set_max_points = False
            self.save()

    def set_points_not_concerned(self):
        """
        This method calculates for an evaluation the total of the points that are considered as not concerned due to
        the choices ticked by the user, either an choice that disabled an other evaluation element or choices not
        possible inside the same evaluation element
        :return: float
        """
        # todo test element weight with values not equal to 1
        evaluation_element_weight = self.get_element_weight()
        sum_points_not_concerned = 0
        for section in self.evaluation.section_set.all():
            for element in section.evaluationelement_set.all():
                # Check this is useful to calculate points not concerned (condition intra or inter)
                if element.has_condition_between_choices() or not element.is_applicable():
                    element_weight = evaluation_element_weight.get_master_element_weight(
                        element.master_evaluation_element
                    )
                    sum_points_not_concerned += (
                        element.calculate_points_not_concerned() * element_weight
                    )
        self.points_not_concerned = sum_points_not_concerned
        self.save()

    def set_exposition_dic(self):
        """
        For an evaluation, it evaluates the risks for which the user is concerned according to his answers to the
        evaluation elements with conditions.

        It creates a dictionary of the risk descriptions as keys (unique) and whether
        the organisation is exposed to the risk (only one element linked to the risk - which can be linked
        to many elements - need to be concerned to trigger the fact the user is concerned to the risk)
        or not, so boolean value.
        By default, there is an exposition to the risks and if the choice which disables the other elements/choices
        is ticked, this means the user is not exposed to these risks.

        Conditions inter/intra = no risk
        """
        exposition_dic = {}
        for section in self.evaluation.section_set.all().order_by("master_section__order_id"):
            for element in section.evaluationelement_set.all().order_by(
                "master_evaluation_element__order_id"
            ):
                if (
                    not element.master_evaluation_element.risk_domain
                    and not element.has_condition_on()
                ):
                    continue
                # Check condition inter elements
                if element.has_condition_on():
                    # No condition inter, so concerned by the risk, register it with evaluation setting conditions
                    if element.is_applicable():
                        if (
                            element.get_element_depending_on().master_evaluation_element.risk_domain
                            not in exposition_dic
                        ):
                            exposition_dic[
                                element.get_element_depending_on().master_evaluation_element.risk_domain
                            ] = [
                                element.get_element_depending_on().master_evaluation_element.id
                            ]

                    # Condition inter, so not concerned by the risk, just register it
                    else:
                        if (
                            element.get_element_depending_on().master_evaluation_element.risk_domain
                            not in exposition_dic
                        ):
                            exposition_dic[
                                element.get_element_depending_on().master_evaluation_element.risk_domain
                            ] = []
                # Check conditions intra element (and not the case with condition intra)
                if element.has_condition_between_choices() and element.is_applicable():
                    # If the choice is ticked, so not concerned by the risk
                    if element.get_choice_condition_intra().is_ticked:
                        # The risk is not in the dictionary (if it already is, just let the list like this)
                        if element.master_evaluation_element.risk_domain not in exposition_dic:
                            exposition_dic[element.master_evaluation_element.risk_domain] = []
                    # Choice not ticked, so concerned by the risk
                    else:
                        # The risk is not in the dictionary
                        if element.master_evaluation_element.risk_domain not in exposition_dic:
                            exposition_dic[element.master_evaluation_element.risk_domain] = [
                                element.master_evaluation_element.id
                            ]
                        # Already the risk in the dictionary
                        else:
                            exposition_dic[
                                element.master_evaluation_element.risk_domain
                            ].append(element.master_evaluation_element.id)
                # Case element with condition intra and not applicable due to conditions inter, still add the risk as
                # not exposed
                if element.has_condition_between_choices() and not element.is_applicable():
                    if element.master_evaluation_element.risk_domain not in exposition_dic:
                        exposition_dic[element.master_evaluation_element.risk_domain] = []
        self.exposition_dic = exposition_dic
        self.save()

    def set_points_obtained(self):
        """
        This method calculates the points obtained in all the sections
        """

        points_obtained = 0
        for section in self.evaluation.section_set.all():
            points_obtained += section.points

        # Add the points not concerned * the coefficient (half points not concerned usually)
        points_obtained += self.points_not_concerned * self.coefficient_scoring_system

        self.points_obtained = round(points_obtained, 4)
        self.save()

    def set_points_to_dilate(self):
        """
        This method calculates the points to dilate: nb obtained points - not concerned points * coeff scoring system
        which is just the sum of the points of the ticked choices according to the scoring

        :return: float
        """
        coefficient = self.coefficient_scoring_system

        self.points_to_dilate = round(
            self.points_obtained - self.points_not_concerned * coefficient, 4
        )
        self.save()

    def set_dilatation_factor(self):
        """
        Calculate the dilatation factor, used to calculate the score of the evaluation

        :return:
        """
        max_points = self.max_points
        pts_not_concerned = self.points_not_concerned
        coeff = self.coefficient_scoring_system
        self.dilatation_factor = round(
            (max_points - pts_not_concerned * coeff) / (max_points - pts_not_concerned), 6
        )
        self.save()

    def set_score(self):
        """
        This method sets the score for the evaluation score object

        :return: None, save the score of the evaluation (float)
        """

        score_after_dilatation = (
            self.dilatation_factor * self.points_to_dilate
            + self.points_not_concerned * self.coefficient_scoring_system
        )
        self.score = round(score_after_dilatation * 100 / self.max_points, 1)
        self.save()

    def process_score_calculation(self):
        """
        Calculate the values for the dynamic fields if the field need_to_calculate is True, which means this is the
        1st calculation or the user modified a choice of a finished evaluation
        """
        if self.evaluation.is_finished:
            if self.need_to_calculate:
                # Order is important
                self.set_points_not_concerned()
                self.set_points_obtained()
                self.set_points_to_dilate()
                self.set_dilatation_factor()
                self.set_score()
                self.set_exposition_dic()
                self.need_to_calculate = False
        else:
            self.score = 0
        self.save()
