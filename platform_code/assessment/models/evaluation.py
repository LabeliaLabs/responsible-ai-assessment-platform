import random

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

from home.models import Organisation
from .assessment import Assessment, get_last_assessment_created
from .upgrade import Upgrade
from .section import Section
from .evaluation_element import MasterEvaluationElement, EvaluationElement
from .choice import MasterChoice, Choice
from .evaluation_score import EvaluationScore


class Evaluation(models.Model):
    """
    The class Evaluation define the object evaluation, which is created by a user and belong to an organization
    An evaluation is defined by an assessment (version) and it is composed of sections, evaluation elements and choices
    An evaluation is a dynamic object
    """

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="evaluations")
    upgraded_from = models.ForeignKey(
        Assessment,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="evaluations_upgraded_from"
    )
    name = models.CharField(
        max_length=200,
        default="Evaluation",
    )
    slug = models.SlugField(unique=False)
    # Set to null if the user delete is account because other users in the orga could still use the evaluation
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    organisation = models.ForeignKey(
        Organisation, null=True, blank=True, on_delete=models.CASCADE
    )  # NEED TO DELETE NULL AND BLANK LATER
    # There are only 2 status choices for an evaluation: done or not done, by default the evaluation is not done
    is_finished = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
    is_deleteable = models.BooleanField(default=True)
    # No score by default, the object will be created when the evaluation is validated by the user
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # This attribute will store the date when the user will validate his evaluation
    finished_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Evaluation {str(self.pk)}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Evaluation, self).save(*args, **kwargs)

    @classmethod
    def create_evaluation(cls, name, assessment, user, organisation, upgraded_from=None):
        """
        To create an evaluation, we need to link it to an assessment (with a defined version)
        and also to an user who does the action and an organisation where the user belongs to
        Note there is no content to the evaluation yet
        If the evaluation is upgraded from an old assessment then upgraded_from contains the reference to it
        otherwise it's null
        :param name: string
        :param assessment: assessment object
        :param user: user
        :param organisation: organisation
        :param upgraded_from: assessment object
        :return:
        """
        if upgraded_from is None:
            evaluation = cls(
                name=name,
                assessment=assessment,
                created_by=user,
                organisation=organisation,
                upgraded_from=assessment.previous_assessment,
            )
        else:
            evaluation = cls(
                name=name,
                assessment=assessment,
                created_by=user,
                organisation=organisation,
                upgraded_from=upgraded_from,
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

    def freeze_evaluation(self):
        """
        Set the is_editable and is_deleteable fields to false
        Used in the labelling process to block the edition and deletion of labelling evaluation
        """
        self.is_deleteable = False
        self.is_editable = False
        self.save()

    def get_list_all_elements(self):
        """
        Returns the list of all the evaluation elements
        """
        list_all_elements = []
        for section in self.section_set.all().order_by("master_section__order_id"):
            for element in section.evaluationelement_set.all().order_by(
                    "master_evaluation_element__order_id"
            ):
                list_all_elements.append(element)
        return list_all_elements

    def has_labelling(self):
        """
        True if the evaluation has a labelling object associated, else Flase
        """
        # TODO tests
        return hasattr(self, 'labelling')

    def get_labelling(self):
        # TODO tests
        if self.has_labelling():
            return self.labelling
        else:
            return None

    def need_justification(self):
        """
        If the evaluation has a labelling object associated and it has the status 'justification'
        so the function returns True, else False
        Used in the templates
        """
        # TODO tests
        if self.has_labelling():
            return self.get_labelling().status == 'justification'

    def get_dict_sections_elements_choices(self):
        dict_sections_elements = {}
        for section in self.section_set.all().order_by(
                "master_section__order_id"):
            dict_sections_elements[section] = {}
            for element in section.evaluationelement_set.all().order_by(
                    "master_evaluation_element__order_id"
            ):
                dict_sections_elements[section][element] = \
                    [choice for choice in element.choice_set.all().order_by("id")]
        return dict_sections_elements

    def create_evaluation_body(self):
        """
        Create the dynamic elements (section, evaluation elements, choices) for an evaluation after the being
        created with EvaluationForm
        All the dynamic objects are based on static objects (master_section, master_evaluation_elements, master_choice)
        according to the assessment's version.
        """
        assessment = self.assessment
        master_section_list = assessment.get_master_sections_list()
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
                    if upgrade_dic["elements"][element_number]["upgrade_status"] == "no_fetch":
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
        created_at = kwargs.get("created_at", timezone.now())
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
            name=self.name,
            assessment=final_assessment,
            organisation=self.organisation,
            user=user_eval,
            upgraded_from=origin_assessment,
        )
        new_eval.created_at = created_at
        new_eval.create_evaluation_body()

        for new_section in new_eval.section_set.all():
            new_section_number = new_section.master_section.get_numbering()
            if upgrade_dic["sections"][new_section_number] == "no_fetch":
                new_section.fetch = False
                new_section.save()
            else:
                # We rely on the upgrade dic to find the matching
                # Two cases: 1 if it fetches itself, or "id" (ex "2") if it fetches an other section
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
                if upgrade_dic["elements"][new_element_number]["upgrade_status"] == "no_fetch":
                    new_element.fetch = False
                    new_element.save()
                else:
                    # Two cases: "1" if it fetches itself, or "id" (ex "1.1") if it fetches an other EE
                    if upgrade_dic["elements"][new_element_number]["upgrade_status"] != 1:
                        older_element_order_id = upgrade_dic["elements"][new_element_number]["upgrade_status"][-1]
                        older_element_section_order_id = upgrade_dic["elements"][new_element_number]["upgrade_status"][
                            -3]
                    else:
                        older_element_order_id = new_element.master_evaluation_element.order_id
                        older_element_section_order_id = new_element.master_evaluation_element.master_section.order_id
                    older_element = EvaluationElement.objects.get(
                        master_evaluation_element__order_id=older_element_order_id,
                        section__master_section__order_id=older_element_section_order_id,
                        section__evaluation=self,
                    )
                    new_element.user_notes = older_element.user_notes
                    new_element.user_justification = older_element.user_justification
                    new_element.is_in_action_plan = older_element.is_in_action_plan
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

    def duplicate_evaluation(self):
        """
        Create the duplicate evaluation (same user, organisation, assessment)
        and complete it with the same answers, notes, justifications than the original one.
        Returns the duplicated evaluation
        """
        new_evaluation = Evaluation.create_evaluation(
            name=f"{self.name}-duplication",
            assessment=self.assessment,
            user=self.created_by,
            organisation=self.organisation
        )
        new_evaluation.create_evaluation_body()
        # Cover all the objects of the original evaluation
        for section in self.section_set.all():
            new_section = Section.objects.get(
                evaluation=new_evaluation,
                master_section__order_id=section.master_section.order_id
            )
            new_section.user_notes = section.user_notes
            new_section.save()
            for evaluation_element in section.evaluationelement_set.all():
                new_element = EvaluationElement.objects.get(
                    section__evaluation=new_evaluation,
                    master_evaluation_element__order_id=evaluation_element.master_evaluation_element.order_id,
                    section__master_section__order_id=section.master_section.order_id
                )
                new_element.user_notes = evaluation_element.user_notes
                new_element.user_justification = evaluation_element.user_justification
                new_element.user_notes_archived = evaluation_element.user_notes_archived
                new_element.is_in_action_plan = evaluation_element.is_in_action_plan
                new_element.save()
                for choice in evaluation_element.choice_set.all():
                    if choice.is_ticked:
                        new_choice = Choice.objects.get(
                            evaluation_element__section__evaluation=new_evaluation,
                            master_choice__order_id=choice.master_choice.order_id,
                            evaluation_element__master_evaluation_element__order_id=  # noqa
                            evaluation_element.master_evaluation_element.order_id,
                            evaluation_element__section__master_section__order_id=section.master_section.order_id
                        )
                        new_choice.set_choice_ticked()
                new_element.set_status()
                new_element.set_points()
            new_section.set_progression()
            new_section.set_points()
        new_evaluation.set_finished()  # If not finished, set to False
        evaluation_score = EvaluationScore.objects.get(evaluation=new_evaluation)
        evaluation_score.need_to_calculate = True
        evaluation_score.save()
        evaluation_score.process_score_calculation()
        return new_evaluation

    def complete_evaluation(self, **kwargs):
        """
        Accepted kwargs key: characteristic
        and values: "min", "max", "normal", "conditions"
        """
        characteristic = kwargs.get("characteristic")
        probability_condition = kwargs.get("probability_condition", 0.3)
        for section in self.section_set.all():
            for evaluation_element in \
                    section.evaluationelement_set.all().order_by("master_evaluation_element__order_id"):
                # Select randomly a choice not setting condition inter and ticked it and save it
                evaluation_element.reset_choices()
                if evaluation_element.is_applicable():
                    if characteristic == "min":
                        evaluation_element.get_choice_min_points().set_choice_ticked()
                    elif characteristic == "max":
                        for choice in evaluation_element.get_choices_list_max_points():
                            choice.set_choice_ticked()
                    else:
                        if characteristic == "conditions":
                            probability_condition = 1
                        elif characteristic == "no_condition":
                            probability_condition = 0
                        # Conditions case
                        probability = random.random()
                        if probability < probability_condition:
                            if evaluation_element.get_list_of_choices_with_conditions():
                                evaluation_element.get_list_of_choices_with_conditions()[0].set_choice_ticked()
                            else:
                                evaluation_element.tick_random_choices_no_condition()

                        # No conditions
                        elif probability >= probability_condition:
                            evaluation_element.tick_random_choices_no_condition()

                    if random.randint(0, 10) > 7:
                        evaluation_element.fill_notes()
                evaluation_element.set_status()
                evaluation_element.set_points()
            if random.randint(0, 10) > 7:
                section.fill_notes()
            section.set_progression()
            section.set_points()
        self.set_finished()
        evaluation_score = EvaluationScore.objects.get(evaluation=self)
        evaluation_score.need_to_calculate = True
        evaluation_score.save()
        evaluation_score.process_score_calculation()
