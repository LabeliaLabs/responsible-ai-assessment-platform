from django.contrib import admin, messages
from django.contrib.postgres.fields import JSONField
from django.shortcuts import redirect

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
    actions = [
        'complete_normal_without_conditions',
        'complete_max_points',
        'complete_min_points',
        'complete_with_conditions'
    ]

    def get_version(self, obj):
        return obj.assessment.version

    def get_score(self, obj):
        evaluation_score = obj.evaluationscore_set.get(evaluation=obj)
        return evaluation_score.score

    def get_progression(self, obj):
        return obj.calculate_progression()

    def complete_normal_without_conditions(self, request, queryset):
        for evaluation in queryset:
            try:
                evaluation.complete_evaluation(characteristic="normal")
                self.message_user(request, f"The evaluation {evaluation} has been completed!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when completing the evaluation{evaluation}",
                    messages.ERROR
                )
        return redirect(request.path_info)

    def complete_max_points(self, request, queryset):
        for evaluation in queryset:
            try:
                evaluation.complete_evaluation(characteristic="max")
                self.message_user(request, f"The evaluation {evaluation} has been completed!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when completing the evaluation{evaluation}",
                    messages.ERROR
                )
        return redirect(request.path_info)

    def complete_min_points(self, request, queryset):
        for evaluation in queryset:
            try:
                evaluation.complete_evaluation(characteristic="min")
                self.message_user(request, f"The evaluation {evaluation} has been completed!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when completing the evaluation{evaluation}",
                    messages.ERROR
                )
        return redirect(request.path_info)

    def complete_with_conditions(self, request, queryset):
        for evaluation in queryset:
            try:
                evaluation.complete_evaluation(characteristic="conditions")
                self.message_user(request, f"The evaluation {evaluation} has been completed!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when completing the evaluation{evaluation}",
                    messages.ERROR
                )
        return redirect(request.path_info)


class EvaluationElementWeightAdmin(admin.ModelAdmin):
    form = EvaluationElementWeightForm
    add_form = EvaluationElementWeightForm
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget, }}
