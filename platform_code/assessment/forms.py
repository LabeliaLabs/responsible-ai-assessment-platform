from ast import literal_eval

from django import forms
from django.forms import ModelForm
from django.forms import widgets
from django.forms.renderers import get_default_renderer
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import (
    Assessment,
    ScoringSystem,
    Choice,
    Evaluation,
    EvaluationElementWeight,
    get_last_assessment_created,
    Section,
)
from .scoring import check_and_valid_scoring_json
from home.models import Organisation
from .utils import markdownify_bold, markdownify_italic, select_label_choice

element_feedback_list = [
    ["element_fit", _("No evaluation element fits to my case")],
    ["element_formulation", _("This evaluation element is poorly formulated")],
    [
        "element_not_concerned",
        _("My organisation is not concerned by this evaluation element"),
    ],
    ["element_typo", _("There is an issue or a typo in the element")],
    ["add_resource", _("I have a new resource to add to this evaluation element")],
    ["resource_issue", _("A resource is not available")],
    ["other", _("Other")],
]

# todo : develop this list
section_feedback_list = [
    ["section_content", _("I find that an evaluation element is not appropriated")],
    ["section_content", _("I would like to propose a new evaluation element")],
    ["section_content", _("I would like to propose a new resource to this section")],
    ["other", _("Other")],
]


class ScoringSystemForm(forms.ModelForm):
    json_file = forms.FileField()

    class Meta:
        model = ScoringSystem

        fields = [
            "name",
            "version",
            "assessment",
            "organisation_type",
            "attributed_points_coefficient",
            "master_choices_weight_json",
        ]

    def __init__(self, *args, **kwargs):
        super(ScoringSystemForm, self).__init__(*args, **kwargs)
        self.fields["json_file"].required = True
        self.fields["json_file"].help_text = _(
            "The json file has to contain the choice ids as keys ('1.1.a' for exemple) and the weight as value"
        )
        if get_last_assessment_created():
            self.fields["assessment"].initial = get_last_assessment_created()
            self.fields["version"].initial = get_last_assessment_created().version
            self.fields["name"].initial = (
                get_last_assessment_created().name + "_scoring"
            )
        self.fields["assessment"].required = True
        self.fields["name"].required = True

        if self.fields["master_choices_weight_json"].initial:
            self.fields["master_choices_weight_json"].initial = literal_eval(
                self.fields["master_choices_weight_json"].initial
            )
        self.fields["master_choices_weight_json"].disabled = True
        self.fields["master_choices_weight_json"].required = False

    def save(self, commit=True, *args, **kwargs):
        """
        Save this form's self.instance object if commit=True. Otherwise, add
        a save_m2m() method to the form which can be called after the instance
        is saved manually at a later time. Return the model instance.
        """
        assessment = self.cleaned_data.get("assessment")
        name = self.cleaned_data.get("name")
        organisation_type = self.cleaned_data.get("organisation_type")
        json_file = self.cleaned_data.get("json_file")
        version = self.cleaned_data.get("version")

        if json_file:
            if json_file.name.endswith("json"):
                try:
                    decoded_file = json_file.read().decode("utf-8")
                except UnicodeDecodeError as e:
                    raise forms.ValidationError(
                        f"Il y a un problème d'encodage dans le json, erreur {e}"
                    )

                success, message = check_and_valid_scoring_json(
                                        decoded_file=decoded_file, assessment=assessment
                                    )
                if not success:
                    raise forms.ValidationError(
                        f"The format of the file is not correct, {message}"
                    )

                self.instance = ScoringSystem(
                    assessment=assessment,
                    version=version,
                    name=name,
                    organisation_type=organisation_type,
                    master_choices_weight_json=literal_eval(decoded_file),
                )
                if commit:
                    # If committing, save the instance and the m2m data immediately.
                    self.instance.save()
                    self._save_m2m()
                else:
                    # If not committing, add a method to the form to allow deferred
                    # saving of m2m data.
                    self.save_m2m = self._save_m2m

            else:
                raise forms.ValidationError(
                    "Le type de fichier est incorrect. Il faut un json."
                )

        return self.instance

    save.alters_data = True


class EvaluationElementWeightForm(forms.ModelForm):
    class Meta:
        model = EvaluationElementWeight

        fields = [
            "name",
            "assessment",
            "organisation_type",
            "master_evaluation_element_weight_json",
        ]

    def __init__(self, *args, **kwargs):

        obj_assessment = Assessment.objects.all().order_by("-created_at")[
            0
        ]  # UGLY, NEED TO CHANGE
        # super(ScoringSystemForm, self).__init__(*args, **kwargs)
        # kwargs.update(initial={
        #     'assessment': obj_assessment
        # })
        super(EvaluationElementWeightForm, self).__init__(*args, **kwargs)
        dic_weight = {}
        for section in obj_assessment.mastersection_set.all():
            for element in section.masterevaluationelement_set.all():
                dic_weight[str(element)] = "1"

        self.fields["master_evaluation_element_weight_json"].initial = dic_weight


class EvaluationForm(forms.ModelForm):
    """
    This form is used when the organisation attached to the evaluation is clearly defined: organisation view
    or after the user created his organisation
    It is used to create evaluations or to edit evaluation name
    """
    class Meta:
        model = Evaluation
        fields = [
            "name",
        ]

    def __init__(self, *args, **kwargs):
        is_name = False
        # If the evaluation name is edited
        if "name" in kwargs:
            name = kwargs.pop("name")
            is_name = True
        super(EvaluationForm, self).__init__(*args, **kwargs)
        if is_name:
            self.fields["name"].initial = name
        self.fields["name"].label = _("Evaluation title")
        self.fields["name"].widget.attrs = {"class": "full-width"}


class EvaluationMutliOrgaForm(ModelForm):
    """
    This form is used to create an evaluation in the user dashboard view
    """
    organisation = forms.ModelChoiceField(queryset=Organisation.objects.all())

    class Meta:
        model = Evaluation
        fields = [
            "name",
            # "organisation",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(EvaluationMutliOrgaForm, self).__init__(*args, **kwargs)
        self.fields["name"].label = _("Evaluation title")
        self.fields["name"].widget.attrs = {"class": "name-eval-field"}
        self.fields["organisation"].label = _("Organisation")
        queryset = Organisation.objects.distinct().filter(
            Q(membership__user=user, membership__role="admin") | Q(membership__user=user, membership__role="editor")
        )
        self.fields["organisation"].queryset = queryset
        self.fields["name"].widget.attrs = {"class": "full-width"}
        self.fields["organisation"].widget.attrs = {"class": "full-width"}


class SectionNotesForm(ModelForm):
    """
    This form edit the section user_notes, used in SectionView
    """
    class Meta:
        model = Section
        fields = ["user_notes"]

    def __init__(self, *args, **kwargs):
        if "user_can_edit" in kwargs:
            user_can_edit = kwargs.pop("user_can_edit")
        else:
            user_can_edit = False
        if "section" in kwargs:
            section = kwargs.pop("section")
        else:
            section = None
        super(SectionNotesForm, self).__init__(*args, **kwargs)
        if section:
            # If the notes are empty
            if section.user_notes is None or section.user_notes == "":
                self.fields["user_notes"] = forms.CharField(
                                                label=_("My notes on the section"),
                                                widget=forms.Textarea(
                                                    attrs={
                                                        "rows": 4,
                                                        "size": 100,
                                                        "width": "100%",
                                                        "class": "textarea textarea-empty",
                                                        "placeholder": _("Enter your notes on the section here."),
                                                    }
                                                ),
                                                required=False,
                                            )
            # If there are already some notes for the section
            elif section.user_notes:
                self.fields["user_notes"] = forms.CharField(
                                                label=_("My notes on the section"),
                                                widget=forms.Textarea(
                                                    attrs={
                                                        "rows": 4,
                                                        "size": 100,
                                                        "width": "100%",
                                                        "class": "textarea textarea-data",
                                                    }
                                                ),
                                                initial=section.user_notes,
                                                required=False,
                                            )
        if not user_can_edit:
            self.fields["user_notes"].disabled = True


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
        super(ChoiceForm, self).__init__(*args, **kwargs)

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

        # If the evaluation element has no user_notes set yet, the default value is displayed
        if evaluation_element.user_notes is None or evaluation_element.user_notes == "":
            notes = forms.CharField(
                label=_("My notes"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 6,
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
            notes = forms.CharField(
                label=_("My notes"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 6,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-data",
                    }
                ),
                initial=evaluation_element.user_notes,
                required=False,
            )

        self.fields["notes"] = notes  # add the notes (empty or not) in the form


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
                    '<li><span class="fa-stack fa-lg result-point"> '
                    '<i class="fa fa-circle fa-stack-2x"></i>'
                    '</span><label class="selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + choice.master_choice.answer_text
                    + "</label></li>"
                )
            else:
                string_html += (
                    '<li><span class="fa-stack fa-lg result-point">'
                    '<i class="fa fa-circle-o fa-stack-2x"></i>'
                    '</span><label class="not-selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + choice.master_choice.answer_text
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
                    '<li><span class="fa-stack fa-lg result-point"> '
                    '<i class="fa fa-circle fa-stack-2x"></i>'
                    '</span><label class="selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + choice.master_choice.answer_text
                    + "</label></li>"
                )
            else:
                string_html += (
                    '<li><span class="fa-stack fa-lg result-point">'
                    '<i class="fa fa-circle-o fa-stack-2x"></i>'
                    '</span><label class="not-selected-choice" for="'
                    + attrs["id"]
                    + "_"
                    + str(order_choice)
                    + '" >'
                    + choice.master_choice.answer_text
                    + "</label></li>"
                )

        string_html += "</ul>"

        return mark_safe(string_html)


class ElementFeedbackForm(forms.Form):
    """
    This form is used to generate the user feedback for an evaluation element
    """

    element_feedback_type = forms.ChoiceField(choices=element_feedback_list)
    text = forms.CharField(
        label=_("Your feedback"),
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "size": 100,
                "width": "95%",
                "class": "feedback-text",
                "placeholder": _("My feedback"),
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ElementFeedbackForm, self).__init__(*args, **kwargs)
        self.fields["element_feedback_type"].widget.attrs[
            "class"
        ] = "select select_feedback"


class SectionFeedbackForm(forms.Form):
    """
    This form is used to generate the user feedback for an evaluation element
    """

    section_feedback_type = forms.ChoiceField(choices=section_feedback_list)
    text = forms.CharField(
        label=_("Your feedback"),
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "size": 100,
                "width": "95%",
                "class": "feedback-text",
                "placeholder": _("My feedback"),
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(SectionFeedbackForm, self).__init__(*args, **kwargs)
        self.fields["section_feedback_type"].widget.attrs[
            "class"
        ] = "select select_feedback"


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

        # If the user has registered the champ user_notes for this element, it is displayed
        if evaluation_element.user_notes != "":
            notes = forms.CharField(
                label=_("My notes"),
                widget=forms.Textarea(
                    attrs={
                        "rows": 3,
                        "size": 100,
                        "width": "100%",
                        "class": "textarea textarea-data",
                    }
                ),
                initial=evaluation_element.user_notes,
                disabled=True,
                required=False,
            )

            self.fields["notes"] = notes  # add the notes (empty or not) in the form


# Import files #


class JsonUploadForm(forms.Form):
    """
    This is the form used to import the assessment : json of the assessment, json of the choice scoring
    and if required, the upgrade json
    By default the upgrade json is not required and it will raise a message/error to the user if it is
    """
    assessment_json_file = forms.FileField()
    scoring_json_file = forms.FileField()
    upgrade_json_file = forms.FileField(required=False, help_text="Json file is the assessment (json) with the version "
                                                                  "convertible into a float (ex: '1.0') and upgrade "
                                                                  "file is the json where all the differences between "
                                                                  "this assessment and the assessments in the DB are "
                                                                  "registered. You don't need to provide and upgrade "
                                                                  "json when it's the first assessment in the database."
                                        )  # help text not displayed
