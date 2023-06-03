import re

from django.db import models

from .evaluation_element import EvaluationElement, MasterEvaluationElement


class MasterChoice(models.Model):
    """
    The class MasterChoice represents the possible choices for each element of evaluation
    It belongs to an master_evaluation_element
    """

    master_evaluation_element = models.ForeignKey(
        MasterEvaluationElement,
        blank=True,
        on_delete=models.CASCADE,
    )
    answer_text = models.TextField()
    order_id = models.CharField(blank=True, null=True, max_length=200)  # can be letters
    # When a master choice can disable the other master choices of the evaluation element, it is set to True
    is_concerned_switch = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.get_numbering() and self.answer_text:
            return f"Master choice {self.get_numbering()} {self.answer_text}"
        elif self.get_numbering() and not self.answer_text:
            return f"Master choice {self.get_numbering()}"
        else:
            return f"Master choice (id {str(self.pk)})"

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
            print(
                f"You need to have an order id for the section "
                f"({self.master_evaluation_element.master_section.order_id}) "
                f", the evaluation element ({self.master_evaluation_element.order_id})"
                f" and the choice ({self.order_id})"
            )
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
            return self.master_choice.get_numbering() + " " + self.master_choice.answer_text
        elif self.master_choice.get_numbering() and not self.master_choice.answer_text:
            return self.master_choice.get_numbering()
        else:
            return f"Choice (id {str(self.pk)})"

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
