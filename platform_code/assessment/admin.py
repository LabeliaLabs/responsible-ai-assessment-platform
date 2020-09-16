import json

from django.contrib import admin, messages
from django.forms import widgets
from django.shortcuts import redirect
from django.urls import path  # Used to import Json
from django.contrib.postgres.fields import JSONField

from .forms import ScoringSystemForm, EvaluationElementWeightForm, JsonUploadForm
from .import_assessment import treat_and_save_dictionary_data
from .models import Evaluation, Assessment, Choice, EvaluationElement, Section, ScoringSystem, MasterChoice,\
    MasterSection, MasterEvaluationElement, ExternalLink, EvaluationElementWeight


class PrettyJSONWidget(widgets.Textarea):
    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
            # these lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in value.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 120)
            return value
        except Exception as e:
            # todo add logs
            print("erreur", e)
            return super(PrettyJSONWidget, self).format_value(value)


class EvaluationElementWeightAdmin(admin.ModelAdmin):
    form = EvaluationElementWeightForm
    add_form = EvaluationElementWeightForm
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget, }}


admin.site.register(MasterSection)
admin.site.register(MasterEvaluationElement)
admin.site.register(MasterChoice)
admin.site.register(ExternalLink)
admin.site.register(EvaluationElementWeight, EvaluationElementWeightAdmin)
admin.site.register(Evaluation)
admin.site.register(Section)
admin.site.register(EvaluationElement)
admin.site.register(Choice)


# Import json Assessment #


class JsonUploadAssessmentAdmin(admin.ModelAdmin):

    change_list_template = "assessment/import-json.html"

    def get_urls(self):
        urls = super().get_urls()
        additional_urls = [
            path("upload-json/", self.upload_json),
        ]
        return additional_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        extra["json_upload_form"] = JsonUploadForm()
        return super(JsonUploadAssessmentAdmin, self).changelist_view(
            request, extra_context=extra
        )

    def upload_json(self, request):
        if request.method == "POST":
            form = JsonUploadForm(request.POST, request.FILES)
            if form.is_valid():
                if request.FILES["json_file"].name.endswith("json"):

                    try:
                        decoded_file = request.FILES["json_file"].read().decode("utf-8")
                    except UnicodeDecodeError as e:
                        self.message_user(
                            request,
                            "There was an error decoding the file:{}".format(e),
                            level=messages.ERROR,
                        )
                        return redirect("admin/")

                    dict_data = json.loads(decoded_file)
                    # print("Upload JSON", type(decoded_file), type(dict_data), dict_data)
                    # Process all the saving of the items (in import_assessment.py)
                    treat_and_save_dictionary_data(dict_data)

                else:
                    self.message_user(
                        request,
                        "Incorrect file type: {}".format(
                            request.FILES["json_file"].name.split(".")[1]
                        ),
                        level=messages.ERROR,
                    )

        else:
            self.message_user(
                request,
                "There was an error in the form {}".format(JsonUploadForm.errors),
                level=messages.ERROR,
            )

        return redirect("admin/")


admin.site.register(Assessment, JsonUploadAssessmentAdmin)


# Import Json Scoring #


class ScoringAdmin(admin.ModelAdmin):

    change_form_template = "assessment/import-json-scoring.html"
    form = ScoringSystemForm
    add_form = ScoringSystemForm
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget, }}

    def get_form(self, request, obj=None, **kwargs):
        """Get the form which will be displayed"""
        # print("GET FORM", request, kwargs)
        if request.user.staff:
            kwargs["form"] = ScoringSystemForm
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ScoringAdmin, self).get_fieldsets(request, obj)
        # print("FILEDSET", fieldsets, fieldsets[0][1], fieldsets[0][1]["fields"])
        return fieldsets


admin.site.register(ScoringSystem, ScoringAdmin)
from django.contrib import admin

# Register your models here.

