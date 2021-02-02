# TODO split this file in a folder with one python file by class

"""
The model is used to create an assessment. The assessment has 2 aspects: the static part
which is not aimed to frequently change (and only by administrators) and the dynamic part
which is the evaluations done by the users.
The static part stores information like names, descriptions, numbering.
The dynamic part won't store many information, just the progression/status, time information (creation, modification)
and the score.
"""

import re

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from home.models import Organisation


def get_last_assessment_created():
    """ Get the last assessment created - If no assessment in DB, returns None """

    if len(list(Assessment.objects.all().order_by("-created_at"))) > 0:
        return list(Assessment.objects.all().order_by("-created_at"))[0]
    else:
        return None


class Assessment(models.Model):
    """ The class Assessment represents the object assessment with
        an ID, a name, a version and a date of creation and a date of last update
        This class stores the static information concerning the assessment (version)
    """

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=200, default="mvp", unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_list_all_choices(self):
        """
        Returns a list of all the choices of the assessment (used to create upgrade json for example)
        :return:
        """
        list_all_choices = []
        for master_section in self.mastersection_set.all().order_by("order_id"):
            for (
                master_element
            ) in master_section.masterevaluationelement_set.all().order_by("order_id"):
                for master_choice in master_element.masterchoice_set.all().order_by(
                    "order_id"
                ):
                    list_all_choices.append(master_choice.get_numbering())
        return list_all_choices

    def get_the_available_languages(self):
        """
        This method returns the list of the languages for the assessment, based on those
        which are registered in the settings
        """
        language_list = []
        for language in get_available_languages():
            if self.check_has_language(language):
                language_list.append(language)
        return language_list

    def check_has_language(self, language):
        """
        Check for each layer of the assessment (Assessment, MasterSection, MasterEvaluationElement, MasterChoice) and
        for the External Link that the fields which are registered to have a translation, are not None
        for the language.
        Returns True if all the fields are not None, else False
        """
        dic = ManageAssessmentTranslation().dic_translated_fields
        # For all the fields which have a translation in the Assessment class, check if they are not None
        for fields in dic["assessment"]:
            if not getattr(self, fields+"_"+language):
                return False
        # Check that all the fields of MasterSection which are registered to have a translation,
        # are not None for the language
        for master_section in self.mastersection_set.all():
            for fields in dic["master_section"]:
                if not getattr(master_section, fields+"_"+language):
                    return False
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for fields in dic["master_evaluation_element"]:
                    if not getattr(master_evaluation_element, fields+"_"+language) and \
                            master_evaluation_element.get_numbering() != "2.2":
                        return False
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for fields in dic["master_choice"]:
                        if not getattr(master_choice, fields+"_"+language):
                            return False
                for external_link in master_evaluation_element.external_links.all():
                    for fields in dic["external_link"]:
                        if not getattr(external_link, fields+"_"+language):
                            return False
        return True

    def get_fields_not_translated(self, language):
        """
        Check for each layer of the assessment (Assessment, MasterSection, MasterEvaluationElement, MasterChoice) and
        for the External Link that the fields which are registered to have a translation, are not None
        for the language. If they are, it is added to the dic_fields, with the obj as key and the field as value.
        The dic is then returned.
        """
        dic_fields = {}
        dic = ManageAssessmentTranslation().dic_translated_fields
        # For all the fields which have a translation in the Assessment class, check if they are not None
        for fields in dic["assessment"]:
            if not getattr(self, fields+"_"+language):
                dic_fields[self] = fields+"_"+language
        # Check that all the fields of MasterSection which are registered to have a translation,
        # are not None for the language
        for master_section in self.mastersection_set.all():
            for fields in dic["master_section"]:
                if not getattr(master_section, fields+"_"+language):
                    dic_fields[master_section] = fields+"_"+language
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for fields in dic["master_evaluation_element"]:
                    if not getattr(master_evaluation_element, fields+"_"+language) and \
                            master_evaluation_element.get_numbering() != "2.2":
                        dic_fields[master_evaluation_element] = fields+"_"+language
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for fields in dic["master_choice"]:
                        if not getattr(master_choice, fields+"_"+language):
                            dic_fields[master_choice] = fields+"_"+language
                for external_link in master_evaluation_element.external_links.all():
                    for fields in dic["external_link"]:
                        if not getattr(external_link, fields+"_"+language):
                            dic_fields[external_link] = fields+"_"+language
        return dic_fields

    def delete_language(self, language):
        """
        This method sets all the fields of the assessment and its body which are in the language to None, the default
        value when the language is not registered.
        Requires that there are at least 2 languages for the assessment.
        """
        # The assessment needs at least to contain the field "name" in the language
        if language in self.get_the_available_languages():
            if len(self.get_the_available_languages()) > 1:
                self.clean_assessment_language(language)
            else:
                raise ValueError(
                    f"You cannot delete the language {language} as the assessment must have at least one language."
                )

    def clean_assessment_language(self, language):
        """
        This method sets all the fields of the assessment and its body which are in the language to None.
        Not that no check is done.
        """
        delete_language_translation_field(self, "assessment", language)
        for master_section in self.mastersection_set.all():
            delete_language_translation_field(master_section, "master_section", language)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                delete_language_translation_field(master_evaluation_element, "master_evaluation_element", language)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    delete_language_translation_field(master_choice, "master_choice", language)
                for resource in master_evaluation_element.external_links.all():
                    delete_language_translation_field(resource, "external_link", language)


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


class Evaluation(models.Model):
    """
    The class Evaluation define the object evaluation, which is created by a user and belong to an organization
    An evaluation is defined by an assessment (version) and it is composed of sections, evaluation elements and choices
    An evaluation is a dynamic object
    """

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200,
        default="Evaluation",
    )
    slug = models.SlugField()
    # Set to null if the user delete is account because other users in the orga could still use the evaluation
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    organisation = models.ForeignKey(
        Organisation, null=True, blank=True, on_delete=models.CASCADE
    )  # NEED TO DELETE NULL AND BLANK LATER
    # There are only 2 status choices for an evaluation: done or not done, by default the evaluation is not done
    is_finished = models.BooleanField(default=False)
    # No score by default, the object will be created when the evaluation is validated by the user
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # This attribute will store the date when the user will validate his evaluation
    finished_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Evaluation, self).save(*args, **kwargs)

    @classmethod
    def create_evaluation(cls, name, assessment, user, organisation):
        """
        To create an evaluation, we need to link it to an assessment (with a defined version)
        and also to an user who does the action and an organisation where the user belongs to
        Note there is no content to the evaluation yet
        :param name: string
        :param assessment: assessment object
        :param user: user
        :param organisation: organisation
        :return:
        """

        evaluation = cls(
            name=name,
            assessment=assessment,
            created_by=user,
            organisation=organisation,
        )
        evaluation.save()
        return evaluation

    def get_absolute_url(self):
        return reverse(
            "assessment:evaluation",
            kwargs={"orga_id": self.organisation.id, "slug": self.slug, "pk": self.pk, },
        )

    def is_upgradable(self):
        """
        Test if an evaluation is upgradable. True if there is an assessment with a latest version
        :return: boolean
        """

        if get_last_assessment_created():
            last_version = float(get_last_assessment_created().version)
            version = float(self.assessment.version)
            return version < last_version
        else:
            return False

    def get_list_all_elements(self):
        list_all_elements = []
        for section in self.section_set.all().order_by("master_section__order_id"):
            for element in section.evaluationelement_set.all().order_by(
                "master_evaluation_element__order_id"
            ):
                list_all_elements.append(element)
        return list_all_elements

    def create_evaluation_body(self):
        """
        Create the dynamic elements (section, evaluation elements, choices) for an evaluation after the being
        created with EvaluationForm
        All the dynamic objects are based on static objects (master_section, master_evaluation_elements, master_choice)
        according to the assessment's version.
        """
        assessment = self.assessment
        master_section_list = list(MasterSection.objects.filter(assessment=assessment))
        for master_section in master_section_list:
            section = Section.create_section(master_section, self)

            # creation of the evaluation elements for each section
            master_evaluation_element_list = list(
                MasterEvaluationElement.objects.filter(master_section=master_section)
            )

            for master_evaluation_element in master_evaluation_element_list:
                evaluation_element = EvaluationElement.create_evaluation_element(
                    master_evaluation_element, section
                )

                # creation of the choices for each evaluation element
                master_choice_list = list(
                    MasterChoice.objects.filter(
                        master_evaluation_element=master_evaluation_element
                    )
                )
                for master_choice in master_choice_list:
                    choice = Choice.create_choice(master_choice, evaluation_element)
                    # Useless as it is already saved in create_choice but we need to use choice for flake
                    choice.save()

                # Set the max points for the evaluation element, after the choices are created
                evaluation_element.set_max_points()
            # After the creation of the evaluation elements, sets max points for the section
            section.set_max_points()
        # Create evaluation score object
        EvaluationScore.create_evaluation_score(evaluation=self)

    def fetch_the_evaluation(self, *args, **kwargs):
        """
        For an evaluation (self), we compare with an other version of assessment and we modify the fetch values for
        the objects of the evaluation.
        This function is used to create a new evaluation while having other with previous version.
        This only set new objects field "fetch" to False in order to have the visual element "NEW"

        :param args:
        :param kwargs: original_assessment (previous assessment)
        :return:
        """
        original_assessment = kwargs.get("origin_assessment")

        # If there are several assessment versions, this assessment is necessary the last one
        if Upgrade.objects.all():
            upgrade = Upgrade.objects.get(
                origin_assessment=original_assessment, final_assessment=self.assessment
            )
            upgrade_dic = upgrade.upgrade_json

            for section in self.section_set.all():
                section_number = section.master_section.get_numbering()
                if upgrade_dic["sections"][section_number] == "no_fetch":
                    section.fetch = False
                    section.save()

                for element in section.evaluationelement_set.all():
                    element_number = element.master_evaluation_element.get_numbering()
                    if upgrade_dic["elements"][element_number] == "no_fetch":
                        element.fetch = False
                        element.save()

                    for choice in element.choice_set.all():
                        choice_number = choice.master_choice.get_numbering()
                        if upgrade_dic["answer_items"][choice_number] == "no_fetch":
                            choice.fetch = False
                            choice.save()

    def upgrade(self, **kwargs):
        """
        The evaluation is upgraded from the current version to the latest. All the notes and the answers are retrieved,
        fetched from the origin version.
        Return the new evaluation (and DO NOT delete the older)
        :return:
        """

        user_request = kwargs.get("user")
        origin_assessment = self.assessment
        final_assessment = get_last_assessment_created()

        # The final assessment must be more recent than the origin, this is check in the views
        upgrade = Upgrade.objects.get(
            origin_assessment=origin_assessment,
            final_assessment=final_assessment
        )
        upgrade_dic = upgrade.upgrade_json

        # Case: the user who created the eval deleted his account but the orga has still users
        if self.created_by:
            user_eval = self.created_by
        else:
            user_eval = user_request

        new_eval = Evaluation.create_evaluation(
            name=self.name + _(" (new version)"),
            assessment=final_assessment,
            organisation=self.organisation,
            user=user_eval,
        )
        new_eval.create_evaluation_body()

        for new_section in new_eval.section_set.all():
            new_section_number = new_section.master_section.get_numbering()
            if upgrade_dic["sections"][new_section_number] == "no_fetch":
                new_section.fetch = False
                new_section.save()
            else:
                # We rely on the upgrade dic to find the matching
                # Tow cases: 1 if it fetches itself, or "id" (ex "2") if it fetches an other section
                if upgrade_dic["sections"][new_section_number] == 1:
                    older_section_order_id = new_section.master_section.order_id
                else:
                    older_section_order_id = upgrade_dic["sections"][new_section_number]
                new_section.user_notes = self.section_set.get(
                    master_section__order_id=older_section_order_id
                ).user_notes
                new_section.save()

            for new_element in new_section.evaluationelement_set.all():
                new_element_number = (
                    new_element.master_evaluation_element.get_numbering()
                )
                if upgrade_dic["elements"][new_element_number] == "no_fetch":
                    new_element.fetch = False
                    new_element.save()
                else:
                    # Two cases: "1" if it fetches itself, or "id" (ex "1.1") if it fetches an other EE
                    if upgrade_dic["elements"][new_element_number] != 1:
                        older_element_order_id = upgrade_dic["elements"][new_element_number][-1]
                        older_element_section_order_id = upgrade_dic["elements"][new_element_number][-3]
                    else:
                        older_element_order_id = new_element.master_evaluation_element.order_id
                        older_element_section_order_id = new_element.master_evaluation_element.master_section.order_id
                    older_element = EvaluationElement.objects.get(
                        master_evaluation_element__order_id=older_element_order_id,
                        section__master_section__order_id=older_element_section_order_id,
                        section__evaluation=self,
                    )
                    new_element.user_notes = older_element.user_notes
                    new_element.save()

                for new_choice in new_element.choice_set.all():
                    new_choice_number = new_choice.master_choice.get_numbering()
                    if upgrade_dic["answer_items"][new_choice_number] == "no_fetch":
                        new_choice.fetch = False
                        new_choice.save()
                    else:
                        # Two cases: "1" if it fetches itself, or "id" (ex "1.1.a") if it fetches an other choice
                        if upgrade_dic["answer_items"][new_choice_number] != 1:
                            older_choice_order_id = upgrade_dic["answer_items"][new_choice_number][-1]
                            older_choice_element_order_id = upgrade_dic["answer_items"][new_choice_number][-3]
                            older_choice_section_order_id = upgrade_dic["answer_items"][new_choice_number][-5]
                        else:
                            # Fetch self
                            older_choice_order_id = new_choice.master_choice.order_id
                            older_choice_element_order_id = new_choice.master_choice.master_evaluation_element.order_id
                            older_choice_section_order_id = \
                                new_choice.master_choice.master_evaluation_element.master_section.order_id
                        older_choice = Choice.objects.get(
                            master_choice__order_id=older_choice_order_id,
                            evaluation_element__master_evaluation_element__order_id=older_choice_element_order_id,
                            evaluation_element__section__master_section__order_id=older_choice_section_order_id,
                            evaluation_element__section__evaluation=self,
                        )
                        new_choice.is_ticked = older_choice.is_ticked
                        new_choice.save()

                new_element.set_points()
                new_element.set_status()
                # Not sure it is useful to save as already done in the methods
                new_element.save()

            new_section.set_points()
            new_section.set_progression()
            new_section.save()

        new_eval.set_finished()
        # we don't set the score here as it is already implemented in the views so we will redirect
        return new_eval

    def set_finished(self):
        """
        If all section are completed, the evaluation is set to finished and the user can validate it
        """

        # We assume the evaluation is not finished
        self.is_finished = False

        list_section = self.section_set.all()
        for section in list_section:
            # If the loop for has no break (all section are 100 % done)
            if section.user_progression < 100:
                break
        # If there is no break encountered in the for loop, which means all sections have progression equal to 100
        else:
            self.is_finished = True
            # If the field is empty, it is the first time the evaluation is finished so it is set to now
            if not self.finished_at:
                self.finished_at = timezone.now()
        self.save()

    def calculate_progression(self):
        """
        Calculate the progression of the evaluation as percentage
        Used in progression bars
        """

        list_section = self.section_set.all()
        sum_progression = 0
        if len(list_section) > 0:
            for section in list_section:
                sum_progression += section.user_progression
            return int(round(sum_progression / len(list_section), 0))
        else:
            return 0


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
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
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

    score = models.FloatField(default=0, blank=True, null=True)

    def __str__(self):
        return "Scoring data for the evaluation " + str(self.evaluation.id)

    @classmethod
    def create_evaluation_score(cls, evaluation):
        evaluation_score = cls(evaluation=evaluation)
        evaluation_score.save()
        evaluation_score.set_max_points()
        evaluation_score.coefficient_scoring_system = evaluation_score.set_coefficient_scoring_system()
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
            assessment=self.evaluation.assessment,
            organisation_type=organisation_type
        )
        if len(list(query_scoring_system)) == 1:
            self.coefficient_scoring_system = query_scoring_system[0].attributed_points_coefficient
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
                    sum_points_not_concerned += element.calculate_points_not_concerned() * element_weight
        self.points_not_concerned = sum_points_not_concerned
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

        self.points_to_dilate = round(self.points_obtained - self.points_not_concerned * coefficient, 4)
        self.save()

    def set_dilatation_factor(self):
        """
        Calculate the dilatation factor, used to calculate the score of the evaluation

        :return:
        """
        max_points = self.max_points
        pts_not_concerned = self.points_not_concerned
        coeff = self.coefficient_scoring_system
        self.dilatation_factor = round((max_points - pts_not_concerned * coeff) / (max_points - pts_not_concerned), 6)
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
                self.need_to_calculate = False
        else:
            self.score = 0
        self.save()


class MasterSection(models.Model):
    """
    This class will store static data concerning the sections of the assessment
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
        if self.order_id:
            return "S" + str(self.order_id) + " " + self.name
        else:
            return self.name

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
    evaluation = models.ForeignKey(Evaluation, blank=True, on_delete=models.CASCADE)
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
    master_section = models.ForeignKey(
        MasterSection, blank=True, on_delete=models.CASCADE
    )
    order_id = models.IntegerField(blank=True, null=True)
    question_text = models.TextField()
    # Number_answers represents the max choices the user can tick
    # By default it is one as it s a single answer and the max is the number of choices of the element
    question_type = models.CharField(
        max_length=200, choices=QUESTION_TYPES, default=RADIO
    )
    explanation_text = models.TextField(blank=True, null=True)
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
        if self.master_section.order_id and self.order_id:
            return (
                "Q"
                + str(self.master_section.order_id)
                + "."
                + str(self.order_id)
                + " "
                + self.name
            )
        else:
            return self.name

    def get_numbering(self):
        if self.order_id and self.master_section.order_id:
            return str(self.master_section.order_id) + "." + str(self.order_id)

    def has_resources(self):
        """ Used to know if a master evaluation element has resources in its external_links, in this case return True,
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
    status = models.BooleanField(default=False)
    points = models.FloatField(default=0)
    # Max points of this evaluation elements according to the scoring used
    max_points = models.FloatField(default=0, blank=True, null=True)
    # This field "fetch" is used for the versioning of assessments
    fetch = models.BooleanField(default=True)
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

    def get_choices_as_tuple(self):
        """ parse the choices field and return a tuple formatted appropriately
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
                        + " | (Lorsque cette réponse est sélectionnée, les autres ne peuvent pas l'être)",
                    )
                )
            else:
                choices_list.append((choice, choice.master_choice.answer_text))
        choices_tuple = tuple(choices_list)
        return choices_tuple

    def reset_choices(self):
        """ Set for all the choices of an evaluation element the attribute 'is_ticked' to False """
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

    def get_list_choices_ticked(self):
        """Returns the list of choices ticked for this evaluation element"""
        list_choices_ticked = []
        list_choices = list(self.choice_set.all())
        for choice in list_choices:
            if choice.is_ticked:
                list_choices_ticked.append(choice)
        return list_choices_ticked

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
        """ True if the evaluation element depends on a choice, else False"""
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
        """Return the evaluation element on which the choice this evaluation element depends on belong  """
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
        # print("IS APPLICABLE", self, self.has_condition_on())
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
        """ Within an evaluation element, if the choices have condition on each other
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
            if str(choice_setting_condition) in list_choices_wanted_ticked and len(list_choices_wanted_ticked) > 1:
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
                    max_points = scoring_system.get_master_choice_points(
                        choice.master_choice
                    )

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


class MasterChoice(models.Model):
    """
    The class MasterChoice represents the possible choices for each element of evaluation
    It belongs to an master_evaluation_element
    """

    master_evaluation_element = models.ForeignKey(
        MasterEvaluationElement, blank=True, on_delete=models.CASCADE,
    )
    answer_text = models.TextField()
    order_id = models.CharField(blank=True, null=True, max_length=200)  # can be letters
    # When a master choice can disable the other master choices of the evaluation element, it is set to True
    is_concerned_switch = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.get_numbering():
            return self.get_numbering() + " " + self.answer_text
        else:
            return self.answer_text

    def get_numbering(self):
        """
        Get the numbering of the master choice, like 1.2.a for the section 1, evaluation element 2 and choice a
        """
        if (
            self.master_evaluation_element.master_section.order_id
            and self.master_evaluation_element.order_id
            and self.order_id
        ):
            return (
                str(self.master_evaluation_element.master_section.order_id)
                + "."
                + str(self.master_evaluation_element.order_id)
                + "."
                + self.order_id
            )
        else:
            print(f"You need to have an order id for the section "
                  f"({self.master_evaluation_element.master_section.order_id}) "
                  f", the evaluation element ({self.master_evaluation_element.order_id})"
                  f" and the choice ({self.order_id})")
            return ""

    def test_numbering(self):
        """
        Test if the numbering format is well respected. Used to import the scoring with json format
        """
        numbering = self.get_numbering()
        # Search if the format is respected in the numbering
        regex = re.findall(r"[0-9].[0-9]{1,2}.[a-zA-Z]", numbering)
        return regex != []

    def get_list_master_element_depending_on(self):
        """
        Returns the list of master evaluation elements depending on this master choice
        :returns list
        """
        return list(self.conditioned_by.all())

    def has_master_element_conditioned_on(self):
        """
        Returns boolean, True if this master choice sets conditions on other master evaluation elements, else False
        """
        return self.get_list_master_element_depending_on()


class Choice(models.Model):
    """
    The class Choice represents the choices made by the user concerning the different elements of evaluation
    The information that the user selects a choice is stored in the boolean field "is_ticked"
    By default this field is set to False and if the user choices this answer, the field is set to True
    """

    master_choice = models.ForeignKey(
        MasterChoice, on_delete=models.CASCADE, blank=True, null=True
    )  # Todo remove blank, null
    evaluation_element = models.ForeignKey(
        EvaluationElement, blank=True, null=True, on_delete=models.CASCADE
    )  # Todo remove null
    is_ticked = models.BooleanField(default=False)
    # This field "fetch" is used for the versioning of assessments
    fetch = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # This field is aimed to contain the username of who ticked the choice
    updated_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        if self.master_choice.get_numbering() and self.master_choice.answer_text:
            return (
                self.master_choice.get_numbering()
                + " "
                + self.master_choice.answer_text
            )
        else:
            return self.master_choice.answer_text

    @classmethod
    def create_choice(cls, master_choice, evaluation_element):
        choice = cls(master_choice=master_choice, evaluation_element=evaluation_element)
        choice.save()
        return choice

    def set_choice_ticked(self):
        self.is_ticked = True
        self.save()

    def set_choice_unticked(self):
        self.is_ticked = False
        self.save()

    def convert_order_id_to_int(self):
        """
        Convert the order id (letter) of the master choice into an int
        97 is subtracted of ord(char) to start with "a" at 0, have "b" to 1, etc
        This function is used to format the widgets in the results page
        :return integer
        """
        order_id = self.master_choice.order_id
        return ord(order_id.lower()) - 97

    def get_evaluation_id(self):
        return self.evaluation_element.section.evaluation.id

    def get_list_element_depending_on(self):
        """
        the list of evaluation_element depending on this choice
        :returns list
        """
        evaluation_id = self.get_evaluation_id()
        list_element = []
        list_master_element = self.master_choice.conditioned_by.all()
        for master_element in list_master_element:
            element = EvaluationElement.objects.get(
                section__evaluation__id=evaluation_id,
                master_evaluation_element=master_element,
            )
            list_element.append(element)
        return list_element

    def has_element_conditioned_on(self):
        """
        For conditions between evaluation elements
        True if this choice has evaluation elements which depends on, else False
        :returns: boolean
        """
        if self.get_list_element_depending_on():
            return True
        else:
            return False

    def has_condition_on(self):
        """
        Used for conditions inside an evaluation element
        For a choice, if one choice in the same evaluation element sets condition on this one, True is return
        Else False
        A choice setting conditions on other choices returns False value
        :return: boolean
        """

        master_evaluation_element = self.master_choice.master_evaluation_element
        for master_choice in master_evaluation_element.masterchoice_set.all():
            if master_choice.is_concerned_switch and master_choice != self.master_choice:
                return True
        return False

    def get_choice_depending_on(self):
        """
        Used for conditions inside an evaluation element
        For a choice, if one choice in the same evaluation element sets condition on this one, returns it,
        else None
        :return:
        """

        # if this choice has an other choice which sets condition on this one
        if self.has_condition_on():
            return self.evaluation_element.get_choice_condition_intra()
        # If the choice has no condition on, so there is no choice to return, normally this case shouldn't happen
        else:
            return None

    def set_conditions_on_other_choices(self):
        """
        Used for conditions inside the evaluation element
        It will return True if this choice sets conditions on other choices and , other choices
        inside the evaluation element are disabled, else it returns False
        :return: boolean
        """

        if self.master_choice.is_concerned_switch:
            return True
        return False

    def is_applicable(self):
        """
        Used for conditions inside the evaluation element
        For a choice, if another choice in the same evaluation element is ticked and disable this one,
        it returns False (this choice is not applicable). Else, the choice is applicable and True is returned
        :return: boolean
        """

        if self.has_condition_on():
            choice_setting_conditions = self.evaluation_element.get_choice_condition_intra()
            if choice_setting_conditions is not None and choice_setting_conditions.is_ticked:
                return False
        return True


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
        return self.name

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
        return self.name

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


class ExternalLink(models.Model):
    # Todo rename as Resources
    """
    This class manages the resources of the assessment. A resource is just a text which will be markdownify when it
    will be displayed.

    """
    WEB_ARTICLE = "web article"
    ACADEMIC_PAPER = "academic paper"
    SOFTWARE = "software"
    TECHNICAL_GUIDE = "technical guide"
    TOOL = "tool"
    CODE_REPOSITORY = "code repository"
    PUBLIC_DECLARATION = "public declaration"
    OFFICIAL_REPORT = "official report"

    RESOURCE_TYPES = (
        (WEB_ARTICLE, "web article"),
        (ACADEMIC_PAPER, "academic paper"),
        (SOFTWARE, "software"),
        (TECHNICAL_GUIDE, "technical guide"),
        (TOOL, "tool"),
        (CODE_REPOSITORY, "code repository"),
        (PUBLIC_DECLARATION, "public declaration"),
        (OFFICIAL_REPORT, "official report"),
    )

    # Name of the resource, will be displayed to the user
    text = models.TextField(max_length=4000, blank=True)
    type = models.CharField(
        choices=RESOURCE_TYPES, default="web_article", max_length=500
    )

    def __str__(self):
        return self.text + " (" + self.type + ")"


def replace_special_characters(sentence):
    """
    This function is used to transform characters in strings, mainly used for urls
    :param sentence:
    :return:
    """
    sentence_modified = sentence.replace("é", "e")
    return sentence_modified.replace(" ", "-")


# Part of the translation management

class ManageAssessmentTranslation:
    classes_with_translated_fields = [
        (Assessment, "assessment"),
        (MasterSection, "master_section"),
        (MasterEvaluationElement, "master_evaluation_element"),
        (MasterChoice, "master_choice"),
        (ExternalLink, "external_link"),
    ]

    dic_translated_fields = {}

    def __init__(self):
        """
        Init the dic_translated_fields with all the fields which are registered to have a translation
        """
        super().__init__()
        for tuple_class in self.classes_with_translated_fields:
            class_name = tuple_class[0]
            self.dic_translated_fields[tuple_class[1]] = \
                [field.name[:-3] for field in class_name._meta.get_fields() if field.name[-3:] == "_en"]


def delete_language_translation_field(obj, obj_name, lang):
    """
    Set the translation to None for all the fields of the object obj.
    The fields are registered in the dic_translation_fields, obj_name mus be a key of this dictionary

    :param obj: object from a class model (Assessment, MasterSection, etc)
    :param obj_name: string, name of the object type ("assessment", "master_section"), must be a key of the dictionary
    :param lang: string, key of the language, either "fr" or "en"
    """
    dic_translated_fields = ManageAssessmentTranslation().dic_translated_fields
    if lang in get_available_languages():
        if obj_name in dic_translated_fields.keys():
            for fields in dic_translated_fields[obj_name]:
                setattr(obj, fields+"_"+lang, None)
            obj.save()
        else:
            raise KeyError(f"The obj_name {obj_name} is not a key of the dictionary of translated fields,"
                           f"available keys: {dic_translated_fields.keys()}")


def get_available_languages():
    """
    This function returns the available languages according to the settings, ex ["fr", "en"]
    """
    return [lang[0] for lang in settings.LANGUAGES]


def is_language_activation_allowed():
    """
    This function covers the assessments of the database and check if they are present in the available languages.
    If they are, return 1, else, return 0 - number instead booleans because it is used in js.
    This is used to display or not a warning in the admin interface when the user activate languages.
    """
    assessment_query = Assessment.objects.all()
    available_languages = get_available_languages()
    for assessment in assessment_query:
        if available_languages != assessment.get_the_available_languages():
            return 0
    return 1
