from django import forms
from django.forms import ModelForm
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from assessment.utils import (
    remove_markdown_bold,
    remove_markdownify_italic,
)
from assessment.models import Choice, Section


class ResultsForm(ModelForm):
    """
    Form to display the results of an evaluation
    This form is only readable and can not be edited
    The widgets of radio and checkbox are edited to add css style
    """

    class Meta:
        model = Choice
        fields = []

    def __init__(self, *args, **kwargs):
        # Catch the evaluation element
        evaluation_element = kwargs.pop("evaluation_element")
        super(ResultsForm, self).__init__(*args, **kwargs)

        if evaluation_element.master_evaluation_element.question_type == "radio":
            choices_tuple = evaluation_element.get_choices_as_tuple()
            # list of all the choices for this evaluation element
            list_choices = list(
                evaluation_element.choice_set.all().order_by("master_choice__order_id")
            )
            question = forms.ChoiceField(
                label="",
                widget=RadioResultsWidget,
                choices=choices_tuple,
                initial=list_choices,
                required=False,
            )  # see if needed
            self.fields[str(evaluation_element.id)] = question

        # If the question_type of the evaluation element is a checkbox, so multiple choices can be selected
        elif evaluation_element.master_evaluation_element.question_type == "checkbox":
            choices_tuple = evaluation_element.get_choices_as_tuple()
            list_choices = list(evaluation_element.choice_set.all())
            question = forms.MultipleChoiceField(
                label="",
                widget=CheckboxResultsWidget,
                choices=choices_tuple,
                initial=list_choices,
            )  # see if needed
            self.fields[str(evaluation_element.id)] = question

        self.add_element_justification_result(evaluation_element)

        # If the user has registered the champ user_notes for this element, it is displayed
        if evaluation_element.user_notes and evaluation_element.user_notes != "":
            notes = forms.CharField(
                label=_("My notes:"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-data-results",
                    }
                ),
                initial=evaluation_element.user_notes,
                disabled=True,
                required=False,
            )
            self.fields["notes"] = notes  # add the notes (empty or not) in the form

    def add_element_justification_result(self, evaluation_element):
        """
        Used during the initialization of a class instance to add a new field in the form for the
        user_justification field of the evaluation_element class model.
        """
        if evaluation_element.user_justification is None or evaluation_element.user_justification == "":
            justification = forms.CharField(
                label=_("Answer justification"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-data-results",
                    }),
                required=False,
            )
        elif evaluation_element.user_justification is not None:
            justification = forms.CharField(
                label=_("Answer justification"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-data-results",
                    }),
                initial=evaluation_element.user_justification,
                required=False,
            )
        self.fields["justification"] = justification


class SectionResultsForm(ModelForm):
    """
    Form to display the results of an evaluation
    This form is only readable and can not be edited
    The widgets of radio and checkbox are edited to add css style
    """

    class Meta:
        model = Section
        fields = []

    def __init__(self, *args, **kwargs):
        # Catch the section
        section = kwargs.pop("section")
        super(SectionResultsForm, self).__init__(*args, **kwargs)

        # If the user has registered the champ user_notes for the section
        if section.user_notes and section.user_notes != "":
            notes = forms.CharField(
                label=_("My section notes:"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-data-results",
                    }
                ),
                initial=section.user_notes,
                disabled=True,
                required=False,
            )

            self.fields["notes"] = notes  # add the notes (empty or not) in the form


class RadioResultsWidget(widgets.CheckboxSelectMultiple):
    """
    Edit the radio items widget to render the selected choices with a purple disk and bold text
    and the not selected choices with purple circle and normal text
    """

    def render(self, name, value, attrs=None, renderer=None):
        string_html = '<ul style="margin: 18px;" id="' + attrs["id"] + '">'
        for choice in value:

            order_choice = choice.convert_order_id_to_int()
            if choice.is_ticked:
                string_html += (
                    '<li class="result-grid"><span class="fa-stack fa-lg result-point"> '
                    '<i class="fa fa-circle fa-stack-2x"></i>'
                    '</span><label class="selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + remove_markdown_bold(remove_markdownify_italic(choice.master_choice.answer_text))
                    + "</label></li>"
                )
            else:
                string_html += (
                    '<li class="result-grid"><span class="fa-stack fa-lg result-point">'
                    '<i class="fa fa-circle-o fa-stack-2x"></i>'
                    '</span><label class="not-selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + remove_markdown_bold(remove_markdownify_italic(choice.master_choice.answer_text))
                    + "</label></li>"
                )

        string_html += "</ul>"

        return mark_safe(string_html)


class CheckboxResultsWidget(widgets.RadioSelect):
    """
    Edit the checkbox item widget to render the selected choices with a purple disk and bold text
    and the not selected choices with purple circle and normal text
    """

    def render(self, name, value, attrs=None, renderer=None):
        string_html = '<ul style="margin: 18px;" id="' + attrs["id"] + '">'
        for choice in value:

            order_choice = choice.convert_order_id_to_int()
            if choice.is_ticked:
                string_html += (
                    '<li class="result-grid"><span class="fa-stack fa-lg result-point"> '
                    '<i class="fa fa-circle fa-stack-2x"></i>'
                    '</span><label class="selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + remove_markdown_bold(remove_markdownify_italic(choice.master_choice.answer_text))
                    + "</label></li>"
                )
            else:
                string_html += (
                    '<li class="result-grid"><span class="fa-stack fa-lg result-point">'
                    '<i class="fa fa-circle-o fa-stack-2x"></i>'
                    '</span><label class="not-selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + remove_markdown_bold(remove_markdownify_italic(choice.master_choice.answer_text))
                    + "</label></li>"
                )

        string_html += "</ul>"

        return mark_safe(string_html)
