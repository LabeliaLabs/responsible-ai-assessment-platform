from django import forms

from assessment.models import (
    Assessment,
    EvaluationElementWeight,
)


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

        super(EvaluationElementWeightForm, self).__init__(*args, **kwargs)
        dic_weight = {}
        for section in obj_assessment.mastersection_set.all():
            for element in section.masterevaluationelement_set.all():
                # Todo just: dic_weight[str(element)] = "1"
                try:
                    dic_weight[str(element)] = "1"
                except Exception as e:
                    print(f"ERROR {e}")
                    pass

        self.fields["master_evaluation_element_weight_json"].initial = dic_weight
