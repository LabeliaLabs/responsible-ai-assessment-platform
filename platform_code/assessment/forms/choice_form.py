from assessment.models import Choice
from assessment.utils import markdownify_bold, markdownify_italic, select_label_choice
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms import ModelForm, widgets
from django.forms.renderers import get_default_renderer
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class ChoiceForm(ModelForm):
    """
    The class ChoiceForm defines the form object used for each evaluation element of the user evaluation
    The form is made up of 2 fields, either a radio or checkbox and a charfield for the user notes
    """

    class Meta:
        model = Choice
        fields = []

    def __init__(self, *args, **kwargs):
        # Catch the evaluation element
        evaluation_element = kwargs.pop("evaluation_element")
        super().__init__(*args, **kwargs)

        # If the question_type of the evaluation element is a radio item
        if evaluation_element.master_evaluation_element.question_type == "radio":
            choices_tuple = evaluation_element.get_choices_as_tuple()
            list_choices_ticked = evaluation_element.get_list_choices_ticked()
            question = forms.ChoiceField(
                label="",
                widget=MarkdownifyRadioChoices,
                choices=choices_tuple,
                initial=list_choices_ticked,  # Initial ticked choices according the database
                required=False,
            )  # see if needed
            self.fields[str(evaluation_element.id)] = question

        # If the question_type of the evaluation element is a checkbox, so multiple choices can be selected
        elif evaluation_element.master_evaluation_element.question_type == "checkbox":
            choices_tuple = evaluation_element.get_choices_as_tuple()
            list_choices_ticked = evaluation_element.get_list_choices_ticked()
            question = forms.MultipleChoiceField(
                label="",
                widget=MarkdownifyMultiselectChoices,
                choices=choices_tuple,
                initial=list_choices_ticked,
                required=False,
            )  # see if needed
            self.fields[str(evaluation_element.id)] = question

        self.add_element_justification(evaluation_element)  # Add the justification field

        # If the evaluation element has no user_notes set yet, the default value is displayed
        if evaluation_element.user_notes is None or evaluation_element.user_notes == "":
            notes = forms.CharField(
                label=_("My notes"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 5,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-empty",
                        "placeholder": _("Enter your notes on the evaluation element here."),
                    }
                ),
                required=False,
            )

        # Elif the user has already registered the champ user_notes for this element, it is displayed as initial
        elif evaluation_element.user_notes is not None:
            form_attr = {
                "rows": 5,
                "size": 100,
                "width": "100%",
                "class": "textarea textarea-data",
            }
            if evaluation_element.user_notes_archived:
                form_attr["disabled"] = "disabled"
                form_attr["class"] += " note-disabled"
            notes = forms.CharField(
                label=_("My notes"),
                widget=forms.Textarea(form_attr),
                initial=evaluation_element.user_notes,
                required=False,
            )

        self.fields["notes"] = notes  # add the notes (empty or not) in the form

    def add_element_justification(self, evaluation_element):
        """
        Used during the initialization of a class instance to add a new field in the form for the
        user_justification field of the evaluation_element class model.
        """
        if (
            evaluation_element.user_justification is None
            or evaluation_element.user_justification == ""
        ):
            justification = forms.CharField(
                label=_("Answer justification"),
                widget=CKEditorWidget(),
                required=False,
            )
        elif evaluation_element.user_justification is not None:
            justification = forms.CharField(
                label=_("Answer justification"),
                widget=CKEditorWidget(),
                initial=evaluation_element.user_justification,
                required=False,
            )
        self.fields["justification"] = justification


class MarkdownifyRadioChoices(widgets.RadioSelect):
    """
    Format the choices of the evaluation elements in order to transform markdown symbols into html tags
    """

    def _render(self, template_name, context, renderer=None):
        if renderer is None:
            renderer = get_default_renderer()
        text = renderer.render(template_name, context)
        for value in select_label_choice(renderer.render(template_name, context)):
            text = text.replace(value, markdownify_italic(markdownify_bold(value)))
        return mark_safe(text)


class MarkdownifyMultiselectChoices(forms.CheckboxSelectMultiple):
    """
    Format the choices of the evaluation elements in order to transform markdown symbols into html tags
    """

    def _render(self, template_name, context, renderer=None):
        if renderer is None:
            renderer = get_default_renderer()
        text = renderer.render(template_name, context)
        for value in select_label_choice(renderer.render(template_name, context)):
            text = text.replace(value, markdownify_italic(markdownify_bold(value)))
        return mark_safe(text)
