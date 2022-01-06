from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from assessment.models import Section


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
        if not user_can_edit or not section.evaluation.is_editable:
            self.fields["user_notes"].disabled = True
