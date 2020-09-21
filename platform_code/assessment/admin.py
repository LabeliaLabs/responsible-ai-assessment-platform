import json

from django.contrib import admin, messages
from django.forms import widgets
from django.shortcuts import redirect
from django.urls import path  # Used to import Json
from django.contrib.postgres.fields import JSONField

from .forms import ScoringSystemForm, EvaluationElementWeightForm, JsonUploadForm
from .import_assessment import (
    treat_and_save_dictionary_data,
    check_upgrade,
    save_upgrade,
)
from .models import (
    Evaluation,
    Assessment,
    Choice,
    EvaluationElement,
    Section,
    ScoringSystem,
    MasterChoice,
    MasterSection,
    MasterEvaluationElement,
    ExternalLink,
    EvaluationElementWeight,
    Upgrade,
    get_last_assessment_created,
)


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
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget,}}


admin.site.register(MasterSection)
admin.site.register(MasterEvaluationElement)
admin.site.register(MasterChoice)
admin.site.register(ExternalLink)
admin.site.register(EvaluationElementWeight, EvaluationElementWeightAdmin)
admin.site.register(Evaluation)
admin.site.register(Section)
admin.site.register(EvaluationElement)
admin.site.register(Choice)
admin.site.register(Upgrade)

# Import json Assessment #


class JsonUploadAssessmentAdmin(admin.ModelAdmin):
    """
    This class defines the assessment json import as well as the upgrade_json import.
    From the assessment json file, we create all the objects it contains.
    If there are more than one assessment in the database, an upgrade json must be provided (refer to the doc
    "multiple_version.md" to see the format). From this upgrade json, the table Upgrade is populated.
    """

    # TODO refacto a little bit this function
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

                    decoded_assessment_file = self.decode_file(
                        request, "json_file"
                    )  # check it works both cases

                    # If there is already an assessment in the data base and we need a
                    # upgrade_json_file to manage the versions
                    if get_last_assessment_created():
                        if "upgrade_json_file" in request.FILES and request.FILES[
                            "upgrade_json_file"
                        ].name.endswith("json"):
                            decoded_upgrade_file = self.decode_file(
                                request, "upgrade_json_file"
                            )  # check it works both cases
                            # Process the import of the assessment
                            try:
                                dict_data = json.loads(decoded_assessment_file)
                            except:
                                self.message_user(
                                    request,
                                    "There is an issue in your json architecture. Please verify you file.",
                                    level=messages.ERROR,
                                )
                                return redirect("admin/")
                            # Process all the saving of the items (in import_assessment.py)
                            # If it fails, there is a message and a redirection to admin
                            try:
                                (
                                    assessment_success,
                                    assessment_save_message,
                                ) = treat_and_save_dictionary_data(dict_data)
                            except:
                                # todo delete the parts of the assessment created (if there are)
                                assessment_success = False
                                assessment_save_message = "The import of the assessment failed. Please, verify your file."
                            if not assessment_success:
                                self.message_user(
                                    request,
                                    assessment_save_message,
                                    level=messages.ERROR,
                                )
                                return redirect("admin/")

                            # Process the import of the upgrade json
                            dict_upgrade_data = json.loads(decoded_upgrade_file)
                            # Verify the validity of the upgrade json and if it s ok, save it in Upgrade
                            upgrade_success, upgrade_message = check_upgrade(
                                dict_upgrade_data
                            )
                            if not upgrade_success:
                                self.message_user(
                                    request, upgrade_message, level=messages.ERROR,
                                )
                                return redirect("admin/")
                            upgrade_save_success, upgrade_save_message = save_upgrade(
                                dict_upgrade_data
                            )
                            if not upgrade_save_success:
                                self.message_user(
                                    request, upgrade_save_success, level=messages.ERROR,
                                )
                                return redirect("admin/")

                            # success in this case ! the assessment and the upgrade items have been created
                            else:
                                self.message_user(
                                    request,
                                    assessment_save_message
                                    + " and "
                                    + upgrade_save_message,
                                    level=messages.SUCCESS,
                                )

                        else:
                            self.message_user(
                                request,
                                "You need to provide a json file (end with '.json') for the upgrade",
                                level=messages.ERROR,
                            )

                    # Else this is the first assessment that we ganna import so we don't need an upgrade_file
                    else:
                        # Process the import of the assessment
                        try:
                            dict_data = json.loads(decoded_assessment_file)
                        except:
                            self.message_user(
                                request,
                                "There is an issue in your json architecture. Please verify you file.",
                                level=messages.ERROR,
                            )
                            return redirect("admin/")
                        # Process all the saving of the items (in import_assessment.py)
                        try:
                            (
                                assessment_success,
                                assessment_save_message,
                            ) = treat_and_save_dictionary_data(dict_data)
                        except:
                            # todo delete the parts of the assessment created (if there are)
                            assessment_success = False
                            assessment_save_message = "The import of the assessment failed. Please, verify your file."

                        if not assessment_success:
                            self.message_user(
                                request, assessment_save_message, level=messages.ERROR,
                            )
                            return redirect("admin/")
                        else:
                            self.message_user(
                                request,
                                assessment_save_message,
                                level=messages.SUCCESS,
                            )

                # Else there is an issue with the assessment json format (which is not a json)
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

    def decode_file(self, request, file_name):
        """
        This method is used to decode json files when they are imported
        :param request: user request
        :param file_name: string
        :return:
        """
        try:
            decoded_file = request.FILES[file_name].read().decode("utf-8")
        except UnicodeDecodeError as e:
            self.message_user(
                request,
                "There was an error decoding the file:{}".format(e),
                level=messages.ERROR,
            )
            return redirect("admin/")
        return decoded_file


admin.site.register(Assessment, JsonUploadAssessmentAdmin)


# Import Json Scoring #


class ScoringAdmin(admin.ModelAdmin):
    change_form_template = "assessment/import-json-scoring.html"
    form = ScoringSystemForm
    add_form = ScoringSystemForm
    formfield_overrides = {JSONField: {"widget": PrettyJSONWidget,}}

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

