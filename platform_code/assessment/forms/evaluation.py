from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.utils import timezone

from home.models import Organisation
from assessment.models import Evaluation


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
        """
        When value is_name in kwargs, it means the evaluation has already a name and the user wants to edit it
        """
        is_name = False
        # If the evaluation name is edited
        if "name" in kwargs:
            name = kwargs.pop("name")
            is_name = True
        super(EvaluationForm, self).__init__(*args, **kwargs)
        if is_name:
            self.fields["name"].initial = name
        else:
            self.fields["name"].initial = _("Evaluation") + " " + str(timezone.now().strftime("%d/%m/%Y"))
        self.fields["name"].label = _("Evaluation title")
        self.fields["name"].widget.attrs = {"class": "full-width center"}


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
        self.fields["name"].widget.attrs = {"class": "full-width center"}
        self.fields["organisation"].widget.attrs = {"class": "full-width center-select"}
        self.fields["name"].initial = _("Evaluation") + " " + str(timezone.now().strftime("%d/%m/%Y"))
