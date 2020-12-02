from django.contrib import admin
from django.contrib.postgres.fields import JSONField

from .utils import PrettyJSONWidget
from assessment.forms import EvaluationElementWeightForm


class EvaluationAdmin(admin.ModelAdmin):
    """

    """
    list_display = ("name",
                    "created_at",
                    "created_by",
                    "organisation",
                    "assessment",
                    "get_version",
                    "is_finished",
                    "get_progression",
                    "get_score",
                    )
    list_filter = (
        "created_at",
        "assessment__version",
        "is_finished",
        "organisation",
    )

    def get_version(self, obj):
        return obj.assessment.version

    def get_score(self, obj):
        evaluation_score = obj.evaluationscore_set.get(evaluation=obj)
        return evaluation_score.score

    def get_progression(self, obj):
        return obj.calculate_progression()


class EvaluationElementWeightAdmin(admin.ModelAdmin):
    form = EvaluationElementWeightForm
    add_form = EvaluationElementWeightForm
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget, }}
