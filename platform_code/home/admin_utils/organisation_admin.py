from django.contrib import admin

from assessment.models import EvaluationScore


class OrganisationAdmin(admin.ModelAdmin):
    """
    Class to custom Organisation in admin interface
    """

    list_display = (
        "name",
        "created_by",
        "creation_date",
        "number_members",
        "evaluations_in_progress",
        "evaluations_finished",
        "last_version",
        "max_score"
    )

    def creation_date(self, obj):
        return obj.created_at.strftime("%d/%m/%Y")

    def number_members(self, obj):
        return obj.count_displayed_members()

    def evaluations_in_progress(self, obj):
        return obj.count_evaluations_finished_or_not(finished=False)

    def evaluations_finished(self, obj):
        return obj.count_evaluations_finished_or_not(finished=True)

    def last_version(self, obj):
        return obj.get_last_assessment_version()

    def max_score(self, obj):
        max_score = 0
        for evaluation in obj.get_list_evaluations():
            evaluation_score = EvaluationScore.objects.get(evaluation=evaluation)
            if evaluation_score.score > max_score:
                max_score = evaluation_score.score
        return max_score
