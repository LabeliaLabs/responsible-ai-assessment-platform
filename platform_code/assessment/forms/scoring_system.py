from ast import literal_eval

from django import forms
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from assessment.models import ScoringSystem, get_last_assessment_created
from assessment.scoring import check_and_valid_scoring_json


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
        self.fields["json_file"].required = False
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
        self.fields["attributed_points_coefficient"].disabled = True

        if self.fields["master_choices_weight_json"].initial:
            self.fields["master_choices_weight_json"].initial = literal_eval(
                self.fields["master_choices_weight_json"].initial
            )
        self.fields["master_choices_weight_json"].disabled = False
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
        modified_json = self.cleaned_data.get("master_choices_weight_json")

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
                # For all the evaluations linked to the assessment & the scoring, need to calculate points max again
                self.set_need_points_max_to_be_calculated()
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
                    "Incorrect file, you need a json."
                )
        # Case no file imported but the json modified
        else:
            try:
                scoring = ScoringSystem.objects.get(assessment=assessment)
                json_before_changes = scoring.master_choices_weight_json
            except (ValueError, MultipleObjectsReturned, ObjectDoesNotExist) as e:
                raise forms.ValidationError(f"The query to get the scoring failed, error {e}")
            instance = super(ScoringSystemForm, self).save(commit=False)  # Commit False does not save the object
            # If there are changes in the json
            if json_before_changes and json_before_changes != modified_json:
                success, message = check_and_valid_scoring_json(json=modified_json, assessment=assessment)
                if not success:
                    raise forms.ValidationError(f"The format of the file is not correct, {message}")
                if success:
                    # Need to calculate again the max score
                    # So change the field need_to_set_max_points for every evaluation score associated
                    self.set_need_points_max_to_be_calculated()
            # Save whether the json has changed or not (may be an other field of the form)
            instance.save()

        return self.instance

    save.alters_data = True

    def set_need_points_max_to_be_calculated(self):
        for evaluation in self.instance.assessment.evaluation_set.all():
            if evaluation.evaluationscore_set.count() == 1:
                evaluation_score = evaluation.evaluationscore_set.all()[0]
                # We do not set the max points now as it can be long (I did not tested)
                # It will be done by user calls
                evaluation_score.need_to_set_max_points = True
                # We also need to calculate again the score !!!
                evaluation_score.need_to_calculate = True
                evaluation_score.save()
            elif evaluation.evaluationscore_set.count() == 0:
                raise ObjectDoesNotExist(f"The evaluation score does not exist for the evaluation"
                                         f" (id {evaluation.id}). "
                                         f"This is not possible so please create one.")
            else:
                raise MultipleObjectsReturned(f"The evaluation (id {evaluation.id}) has multiple "
                                              f"evaluation score. "
                                              f"This is not possible, so please clean it to keep only one.")
