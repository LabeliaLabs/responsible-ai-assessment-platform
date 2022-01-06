from django import forms
from django.utils.translation import gettext_lazy as _


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

section_feedback_list = [
    ["section_content", _("I find that an evaluation element is not appropriated")],
    ["section_content", _("I would like to propose a new evaluation element")],
    ["section_content", _("I would like to propose a new resource to this section")],
    ["other", _("Other")],
]


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
        ] = "select select-feedback-popin"


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
        ] = "select select-feedback-popin"
