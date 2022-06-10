import csv
from datetime import date

from django.contrib import admin
from django.utils.translation import gettext as _
from django.http import HttpResponse

from assessment.models import EvaluationScore


class OrganisationAdmin(admin.ModelAdmin):
    """
    Class to custom Organisation in admin interface
    """
    actions = ["export_data_to_csv"]

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

    def export_data_to_csv(self, request, queryset):
        """
        Action which for the selected organisations, export a csv file with all the information about the
        evaluations of the organisation.
        """
        response = HttpResponse(content_type='text/csv')
        today = date.today().strftime("%Y-%m-%d")
        response['Content-Disposition'] = f'attachment; filename="organisation-data-{today}.csv"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['organisation_name', 'organisation_id', 'evaluation_name', 'evaluation_id',
                         'assessment_version', 'created_by', 'is_finished', 'finished_at', 'section_numbering',
                         'section_fetch', 'section_notes', 'element_numbering', 'element_is_applicable',
                         'element_fetch', 'element_notes', 'choice_numbering', 'choice_fetch', 'is_ticked',
                         ])
        for organisation in queryset:
            for evaluation in organisation.evaluation_set.all():
                for section in evaluation.section_set.all().order_by("master_section__order_id"):
                    for element in section.evaluationelement_set.all().order_by("master_evaluation_element__order_id"):
                        for choice in element.choice_set.all().order_by("master_choice__order_id"):
                            writer.writerow([organisation.name, organisation.id,
                                             evaluation.name, evaluation.id, evaluation.assessment.version,
                                             evaluation.created_by, evaluation.is_finished, evaluation.finished_at,
                                             section.master_section.get_numbering(), section.fetch, section.user_notes,
                                             element.master_evaluation_element.get_numbering(), element.is_applicable(),
                                             element.fetch, element.user_notes,
                                             choice.master_choice.get_numbering(), choice.fetch, choice.is_ticked,
                                             ])
        return response
    export_data_to_csv.short_description = _("Export the organisation evaluations as CSV file")
