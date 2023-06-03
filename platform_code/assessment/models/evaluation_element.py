import random

from ckeditor.fields import RichTextField
from django.db import models
from django.utils.translation import gettext_lazy as _

from .element_change_log import ElementChangeLog
from .evaluation_element_weight import EvaluationElementWeight
from .scoring_system import ScoringSystem
from .section import MasterSection, Section


class MasterEvaluationElement(models.Model):
    """
    The class MasterElement represents the elements of evaluation. These are static objects
    as the content is not aimed to change by users.
    It also define if the evaluation element depends on a choice to be displayed
    """

    RADIO = "radio"
    CHECKBOX = "checkbox"

    QUESTION_TYPES = (
        (RADIO, "radio"),
        (CHECKBOX, "checkbox"),
    )

    # The name is the title of the element of evaluation which can be blank
    name = models.CharField(max_length=1000, blank=True, null=True)
    master_section = models.ForeignKey(MasterSection, blank=True, on_delete=models.CASCADE)
    order_id = models.IntegerField(blank=True, null=True)
    question_text = models.TextField()
    # Number_answers represents the max choices the user can tick
    # By default it is one as it s a single answer and the max is the number of choices of the element
    question_type = models.CharField(max_length=200, choices=QUESTION_TYPES, default=RADIO)
    explanation_text = models.TextField(blank=True, null=True)
    risk_domain = models.TextField(blank=True, null=True)
    # External links are the resources
    external_links = models.ManyToManyField(
        "assessment.ExternalLink", blank=True, related_name="external_links"
    )
    depends_on = models.ForeignKey(
        "assessment.MasterChoice",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="conditioned_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order_id"]

    def __str__(self):
        if self.master_section.order_id and self.order_id and self.name:
            return (
                "Master Q"
                + str(self.master_section.order_id)
                + "."
                + str(self.order_id)
                + " "
                + self.name
            )
        elif self.master_section.order_id and self.order_id and not self.name:
            return f"Master evaluation element Q{str(self.master_section.order_id)}.{str(self.order_id)}"
        else:
            return f"Master evaluation element (id {str(self.pk)})"

    def get_verbose_name(self):
        if self.master_section.order_id and self.order_id and self.name:
            return (
                "Q"
                + str(self.master_section.order_id)
                + "."
                + str(self.order_id)
                + " "
                + self.name
            )

    def get_numbering(self):
        if self.order_id and self.master_section.order_id:
            return str(self.master_section.order_id) + "." + str(self.order_id)

    def has_resources(self):
        """Used to know if a master evaluation element has resources in its external_links, in this case return True,
        else, if it has no external linksor only explanations links, return False"""
        return list(self.external_links.all()) != []


class EvaluationElement(models.Model):
    """
    The class Element is designed to store the data concerning the user's evaluation

    """

    master_evaluation_element = models.ForeignKey(
        MasterEvaluationElement, on_delete=models.CASCADE, blank=True
    )  # TODO remove blank

    section = models.ForeignKey(Section, blank=True, on_delete=models.CASCADE)
    user_notes = models.TextField(blank=True, null=True, max_length=20000)
    user_notes_archived = models.BooleanField(default=False)
    user_justification = RichTextField(blank=True, null=True, max_length=20000)
    status = models.BooleanField(default=False)
    points = models.FloatField(default=0)
    # Max points of this evaluation elements according to the scoring used
    max_points = models.FloatField(default=0, blank=True, null=True)
    # This field "fetch" is used for the versioning of assessments
    fetch = models.BooleanField(default=True)
    is_in_action_plan = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if (
            self.master_evaluation_element.master_section.order_id
            and self.master_evaluation_element.order_id
        ):
            return (
                "Q"
                + str(self.master_evaluation_element.master_section.order_id)
                + "."
                + str(self.master_evaluation_element.order_id)
                + " "
                + self.master_evaluation_element.name
            )
        else:
            return self.master_evaluation_element.name

    @classmethod
    def create_evaluation_element(cls, master_evaluation_element, section):
        evaluation_element = cls(
            master_evaluation_element=master_evaluation_element, section=section
        )
        evaluation_element.save()
        return evaluation_element

    def get_choices_list(self):
        """
        Return the list of choices of the evaluation element
        """
        return [choice for choice in self.choice_set.all()]

    def get_choice_min_points(self):
        """
        Get the choice of the element with the minimum points
        It doesn't count the choices with conditions inter or intra as they always count 0 points
        but give automatically half the points
        """
        scoring_choices = self.get_scoring_system().master_choices_weight_json
        return sorted(
            self.get_list_of_choices_without_conditions(),
            key=lambda choice: float(scoring_choices[choice.master_choice.get_numbering()]),
        )[0]

    def get_choices_list_max_points(self):
        """
        Get the choice of the element with the max points
        """
        scoring_choices = self.get_scoring_system().master_choices_weight_json
        choices_list = []
        if self.master_evaluation_element.question_type == "radio":
            choices_list = [
                sorted(
                    self.get_list_of_choices_without_conditions(),
                    key=lambda choice: float(
                        scoring_choices[choice.master_choice.get_numbering()]
                    ),
                )[-1]
            ]
        else:
            choices_list = self.get_list_of_choices_without_conditions()
        return choices_list

    def get_list_of_choices_without_condition_inter(self):
        """
        Return the list of the choices of the evaluation element which do not set condition on
        an other evaluation element
        """
        return [
            choice
            for choice in self.choice_set.all()
            if not choice.has_element_conditioned_on()
        ]

    def get_list_of_choices_without_conditions(self):
        """
        Return the list of the choices of the evaluation element which do not set condition intra or inter
        """
        return [
            choice
            for choice in self.choice_set.all()
            if not choice.has_element_conditioned_on()
            and not choice.set_conditions_on_other_choices()
        ]

    def get_list_of_choices_with_conditions(self):
        """
        Return the list of the choices of the evaluation element which has conditions on
        an other evaluation element or condition on other choices
        """
        return [
            choice
            for choice in self.choice_set.all()
            if choice.has_element_conditioned_on() or choice.set_conditions_on_other_choices()
        ]

    def get_choices_as_tuple(self):
        """parse the choices field and return a tuple formatted appropriately
        for the 'choices' argument of a form widget."""
        choices_query = self.choice_set.all().order_by("master_choice__order_id")
        choices_list = []
        for choice in choices_query:
            # case it s a choice which is incompatible with other choices, we add some text for the user
            if choice.set_conditions_on_other_choices():
                choices_list.append(
                    (
                        choice,
                        choice.master_choice.answer_text
                        + _(
                            " | (When this answer is selected, the others cannot be selected)"
                        ),
                    )
                )
            else:
                choices_list.append((choice, choice.master_choice.answer_text))
        choices_tuple = tuple(choices_list)
        return choices_tuple

    def reset_choices(self):
        """Set for all the choices of an evaluation element the attribute 'is_ticked' to False"""
        list_choices = list(self.choice_set.all())
        for choice in list_choices:
            choice.set_choice_unticked()
        self.set_status()
        self.save()

    def are_notes_filled(self):
        """
        True is there are notes saved for the evaluation element, else False
        :return: boolean
        """
        if self.user_notes:
            return True
        else:
            return False

    def fill_notes(self):
        """
        Fill the notes with random string
        """
        words = [
            "Jean-Pierre",
            "mange",
            "un lapin dodu",
            "avec ses convives",
            "dans sa cuisine",
        ]
        random.shuffle(words)
        self.user_notes = " ".join(words)
        self.save()

    def get_list_choices_ticked(self):
        """Returns the list of choices ticked for this evaluation element"""
        list_choices_ticked = []
        list_choices = list(self.choice_set.all())
        for choice in list_choices:
            if choice.is_ticked:
                list_choices_ticked.append(choice)
        return list_choices_ticked

    def tick_random_choices_no_condition(self):
        """
        Randomly tick choices of the evaluation element (one if radio, random number if checkbox).
        It only ticks choices without conditions intra/inter.
        """
        if self.master_evaluation_element.question_type == "checkbox":
            # Select random number of choices without condition and tick them
            choice_list = self.get_list_of_choices_without_conditions()
            if choice_list:
                random_int = random.randint(1, len(choice_list))
                random_list = random.sample(choice_list, random_int)
                for i, choice_to_tick in enumerate(random_list):
                    choice_to_tick.set_choice_ticked()
        else:
            # Select one choice without condition and tick
            random.choice(self.get_list_of_choices_without_conditions()).set_choice_ticked()

    def are_choices_valid(self, choice_list):
        """
        Check that the strings contained in the list (choice_list) match with the evaluation element choices.
        This is used during the answer validation.

        :param choice_list: list of strings
        :results: boolean
        """
        # Todo tests
        numbering = self.master_evaluation_element.get_numbering()
        # Check that the 1st 3 characters (choice numbering) match with the element numbering
        return all(choice[:3] == numbering for choice in choice_list)

    def set_status(self):
        """True is one choice is ticked, else False"""
        if len(self.get_list_choices_ticked()) != 0:
            self.status = True
        else:
            self.status = False
        self.save()

    def get_number_possible_answers(self):
        """Number of possible answers for an evaluation element"""
        possible_answers = 0
        if self.master_evaluation_element.question_type == "radio":
            possible_answers = 1
        elif self.master_evaluation_element.question_type == "checkbox":
            # max possible answers when it s a checkbox is the number of choices
            possible_answers = len(list(self.choice_set.all()))
        return possible_answers

    def get_master_choice_depending_on(self):
        """:returns master_choice if evaluation element depends a master_choice , else None"""
        return self.master_evaluation_element.depends_on

    def has_condition_on(self):
        """True if the evaluation element depends on a choice, else False"""
        if self.get_master_choice_depending_on() is None:
            return False
        else:
            return True

    def get_choice_depending_on(self):
        """:returns choice if the evaluation element depends on a choice"""
        evaluation_id = self.section.evaluation.id
        if self.has_condition_on():
            master_choice = self.get_master_choice_depending_on()
            choice = master_choice.choice_set.filter(
                evaluation_element__section__evaluation__id=evaluation_id
            )[0]
            return choice
        else:
            return None

    def get_element_depending_on(self):
        """Return the evaluation element on which the choice this evaluation element depends on belong"""
        if self.has_condition_on():
            choice = self.get_choice_depending_on()
            return choice.evaluation_element
        return None

    def is_applicable(self):
        """
        For condition inter evaluation elements
        False if the choice this evaluation element depends on is ticked, else True
        :returns boolean
        """
        if self.has_condition_on():
            choice = self.get_choice_depending_on()
            if choice.is_ticked:
                return False
            else:
                return True
        else:
            return True

    def has_condition_on_other_elements(self):
        """
        For this element, if one of his choice set conditions for other element,
        return True, else False
        """
        for choice in self.choice_set.all():
            if choice.has_element_conditioned_on():
                return True
        return False

    def get_choice_setting_conditions_on_other_elements(self):
        """
        Get the choice setting conditions on other evaluation elements
        """
        for choice in self.choice_set.all():
            if choice.has_element_conditioned_on():
                return choice
        return None

    def has_condition_between_choices(self):
        """Within an evaluation element, if the choices have condition on each other
        if at least one choice disables other choices, return True, else False
        :return boolean
        """
        for choice in self.choice_set.all():
            if choice.master_choice.is_concerned_switch:
                return True
        return False

    def get_choice_condition_intra(self):
        """
        For condition intra evaluation element, get the choice which set condition on other, else None
        :return: choice or None
        """
        for choice in self.choice_set.all():
            if choice.master_choice.is_concerned_switch:
                return choice
        return None

    def get_list_choices_with_condition(self):
        """
        Used for conditions inside the evaluation element
        This method returns the list of choices of this evaluation element which have condition on.
        This list is empty if the evaluation element has no intra condition
        :return: list
        """
        list_disabled_choices = []
        if self.has_condition_between_choices():
            for choice in self.choice_set.all():
                # if the choice has conditions on, we add it to the list
                if choice.has_condition_on():
                    list_disabled_choices.append(choice)
        return list_disabled_choices

    def are_conditions_between_choices_satisfied(self, list_choices_wanted_ticked):
        """
        This function checks, for an evaluation element with conditions between choices,
         if the choices ticked are possible
        regarding the conditions between the choices inside this evaluation element, if there are conditions.
        Return True if the choices ticked respects the conditions, else False

        WARNING : list_choices_wanted_ticked is a list of string, not a list of choices !!

        :return: boolean

        """
        # If the evaluation element has conditions between choices
        if self.has_condition_between_choices():
            choice_setting_condition = self.get_choice_condition_intra()
            # If the choice setting condition intra is in the list (already ticked or wanted to be)
            # It must be alone, other way the combination is not valid
            if (
                str(choice_setting_condition) in list_choices_wanted_ticked
                and len(list_choices_wanted_ticked) > 1
            ):
                return False
        return True

    def set_points(self):
        """
        This method sets the points attribute of an evaluation element
        This is calculated by adding the weight of the choices set to True
        and then by multiplying the sum by the weight of the evaluation element in
        the dic of EvaluationElementWeight
        """

        scoring_system = self.get_scoring_system()
        master_evaluation_element_weight = self.get_master_evaluation_element_weight()
        points_element = 0

        # If the evaluation element is applicable
        if self.is_applicable():
            for choice in self.choice_set.all():
                if choice.is_ticked:
                    points_element += scoring_system.get_master_choice_points(
                        choice.master_choice
                    )

                    # Manage the case the choice disable other evaluation element to set their points to 0
                    if choice.has_element_conditioned_on():
                        # todo check if it is this if which cause flake issue
                        list_element_disabled = choice.get_list_element_depending_on()
                        for element in list_element_disabled:
                            element.points = 0
                            # reset the choices of the elements disabled
                            element.reset_choices()
                            element.save()

            # Multiply the sum of the choices weight by the evaluation element weight
            element_weight = master_evaluation_element_weight.get_master_element_weight(
                self.master_evaluation_element
            )
            points_element = points_element * element_weight

            # check if it works
            # case there are conditions : no choice is ticked or the choice ticked sets conditions on other choice
            # so no points

        # Not useful but protection
        if not self.is_applicable():
            points_element = 0

        self.points = points_element
        self.save()

    def get_scoring_system(self):
        """
        :return scoring system object
        """

        assessment = self.section.evaluation.assessment
        # organisation_type = self.section.evaluation.orga_id.type_orga  # Not implemented yet
        organisation_type = "entreprise"
        # set the default value in the existing scoring system
        scoring_system = ScoringSystem.objects.filter(
            assessment=assessment, organisation_type=organisation_type
        )[0]
        # check if get is not better
        return scoring_system

    def get_dic_weight_scoring_system(self):
        """
        It loads the json of the weights of each master_choice for the scoring system of the evaluation and returns
        it as a dictionary
        :return: dictionary
        """

        scoring_system = self.get_scoring_system()
        return scoring_system.master_choices_weight_json

    def get_master_evaluation_element_weight(self):
        assessment = self.section.evaluation.assessment
        # organisation_type = self.section.evaluation.orga_id.type_orga  # Not implemented yet
        # set the default value in the existing scoring system
        organisation_type = "entreprise"
        evaluation_element_weight = EvaluationElementWeight.objects.filter(
            assessment=assessment, organisation_type=organisation_type
        )[0]
        return evaluation_element_weight

    def get_coeff_scoring(self):
        """
        This method returns the coeff of the scoring system, used to know the percentage
         of points non concerned attributed
        :return: float
        """

        scoring_system = self.get_scoring_system()
        return scoring_system.attributed_points_coefficient

    def set_max_points(self):
        """
        Initiate a method to calculate the max points possible to an element of evaluation if the user is concerned by
        everything.
        Note that choices which have conditions inter/intra have necessarily 0 points associated

        :return: float
        """

        max_points = 0
        scoring_system = self.get_scoring_system()

        if self.master_evaluation_element.question_type == "radio":
            for choice in self.choice_set.all():
                # We take the max of the weight attributed to a choice of this evaluation element
                if scoring_system.get_master_choice_points(choice.master_choice) > max_points:
                    max_points = scoring_system.get_master_choice_points(choice.master_choice)

        # it is a checkbox
        elif self.master_evaluation_element.question_type == "checkbox":
            for choice in self.choice_set.all():
                # we sum their weight
                max_points += scoring_system.get_master_choice_points(choice.master_choice)

        self.max_points = max_points
        self.save()

    def calculate_points_not_concerned(self):
        """
        For an evaluation element, calculates the points that are considered as non concerned
        We do not applied the coefficient of Scoring System yet (to split the points to dilate)
        And apply the fact that the evaluation element can be weighted
        :return: float
        """

        sum_points_not_concerned = 0
        master_evaluation_element_weight = self.get_master_evaluation_element_weight()

        # if the evaluation element is applicable and there are conditions between choices inside this
        # evaluation element
        if self.is_applicable() and self.has_condition_between_choices():
            for choice in self.choice_set.all():
                # if the choice which sets conditions on other choices is ticked
                if choice.set_conditions_on_other_choices() and choice.is_ticked:
                    # the points not concerned are the max points possible for this evaluation element
                    sum_points_not_concerned = self.max_points

        # If the evaluation element is not applicable,
        # this means that it is due to an answer in a previous evaluation element
        elif not self.is_applicable():
            # we calculate the max possible points of this evaluation element
            sum_points_not_concerned = self.max_points

        # We return the sum_points_not_concerned weighted by the evaluation element weight
        return (
            sum_points_not_concerned
            * master_evaluation_element_weight.get_master_element_weight(
                self.master_evaluation_element
            )
        )

    def get_element_change_log(self):
        """
        Returns the change log object using the associated evaluation element numbering, current assessment and previous
        assessment version.
        there are two cases we need to consider:
         - if this is a new evaluation then we should use the previous_assessment from the Assessment class
         and not upgraded_from of the class Evaluation because it will be null
         - if this is an upgraded evaluation then we will use the upgraded_from object
        """
        if self.section.evaluation.upgraded_from:
            try:
                change_log = ElementChangeLog.objects.get(
                    eval_element_numbering=self.master_evaluation_element.get_numbering(),
                    previous_assessment=self.section.evaluation.upgraded_from,
                    assessment=self.section.evaluation.assessment,
                )
            except (ElementChangeLog.DoesNotExist, ElementChangeLog.MultipleObjectsReturned):
                change_log = None
        else:
            try:
                change_log = ElementChangeLog.objects.get(
                    eval_element_numbering=self.master_evaluation_element.get_numbering(),
                    previous_assessment=self.section.evaluation.assessment.previous_assessment,
                    assessment=self.section.evaluation.assessment,
                )
            except (ElementChangeLog.DoesNotExist, ElementChangeLog.MultipleObjectsReturned):
                change_log = None

        return change_log

    def get_change_log_pastille(self):
        """
        Returns the pastille of the change log related to this evaluation element
        """
        return self.get_element_change_log().pastille

    def get_change_log_edito(self):
        """
        Returns the edito of the change log related to this evaluation element
        """
        return self.get_element_change_log().edito

    def hide_change_log(self):
        """
        Set the visibility attribute of the change log to False so the pastille and the edito won't be displayed
        """
        self.get_element_change_log().hide()

    def display_change_log(self):
        """
        Set the visibility attribute of the change log to True so the pastille and the edito will be displayed
        """
        self.get_element_change_log().display()

    def is_change_log_visible(self):
        """
        Check if the change log is visible, returns true or false
        """
        return self.get_element_change_log().visibility
