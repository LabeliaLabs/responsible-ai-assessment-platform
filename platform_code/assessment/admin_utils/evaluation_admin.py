from django.contrib import admin, messages
from django.db.models import JSONField
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
        'complete_normal',
        'complete_without_conditions',
        'complete_max_points',
        'complete_min_points',
        'complete_with_conditions',
        'upgrade_evaluation',
    ]

    def get_version(self, obj):
        return obj.assessment.version

    def get_score(self, obj):
        evaluation_score = obj.evaluationscore_set.get(evaluation=obj)
        return evaluation_score.score

    def get_progression(self, obj):
        return obj.calculate_progression()

    def complete_normal(self, request, queryset):
        for evaluation in queryset:
            try:
                evaluation.complete_evaluation(characteristic="normal", probability_condition=0.8)
                self.message_user(request, f"The evaluation {evaluation} has been completed!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when completing the evaluation{evaluation}",
                    messages.ERROR
                )
        return redirect(request.path_info)

    def complete_without_conditions(self, request, queryset):
        for evaluation in queryset:
            try:
                evaluation.complete_evaluation(characteristic="no_condition")
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

    def upgrade_evaluation(self, request, queryset):
        for evaluation in queryset:
            if evaluation.is_upgradable():
                try:
                    new_eval = evaluation.upgrade(user=evaluation.created_by)
                    self.message_user(request,
                                      f"The evaluation {evaluation} ({evaluation.calculate_progression()}%)"
                                      f" has been upgraded from the version "
                                      f"{evaluation.assessment.version} to version "
                                      f"{new_eval.assessment.version} and has "
                                      f"{new_eval.calculate_progression()}% of progression",
                                      messages.SUCCESS)
                except Exception as e:
                    self.message_user(
                        request,
                        f"An error occurred, {e}, when upgrading the evaluation {evaluation}",
                        messages.ERROR
                    )
            else:
                self.message_user(
                    request,
                    f"The evaluation {evaluation} is not upgradable (version {evaluation.assessment.version})",
                    messages.WARNING
                )
        return redirect(request.path_info)


class EvaluationElementWeightAdmin(admin.ModelAdmin):
    form = EvaluationElementWeightForm
    add_form = EvaluationElementWeightForm
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget, }}
