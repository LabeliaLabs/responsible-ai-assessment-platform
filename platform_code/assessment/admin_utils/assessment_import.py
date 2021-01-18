import json
from ast import literal_eval

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import path  # Used to import Json
from django.utils.translation import gettext as _

from assessment.forms import JsonUploadForm, ImportAssessmentNewLanguageForm
from assessment.import_assessment import (
    treat_and_save_dictionary_data,
    check_upgrade,
    save_upgrade,
    save_new_assessment_language,
)
from assessment.models import (
    ScoringSystem,
    get_last_assessment_created,
    Assessment,
)
from assessment.scoring import check_and_valid_scoring_json


class JsonUploadAssessmentAdmin(admin.ModelAdmin):
    """
    This class defines the assessment json import, the choice scoring json import as well as the upgrade_json import.
    From the assessment json file, we create all the objects it contains.
    If there are more than one assessment in the database, an upgrade json must be provided (refer to the doc
    "multiple_version.md" to see the format). From this upgrade json, the table Upgrade is populated.
    """
    actions = ['add_new_language_assessment']
    change_list_template = "assessment/admin/import-json.html"

    def get_urls(self):
        urls = super().get_urls()
        additional_urls = [
            path("upload-json/", self.upload_json),
            path("<int:id>/add-assessment-language",
                 self.import_assessment_new_language,
                 name='add-assessment-language',)
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
                if request.FILES["assessment_json_file"].name.endswith("json"):
                    decoded_assessment_file = self.decode_file(
                        request, "assessment_json_file"
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
                            except json.JSONDecodeError as e:
                                self.message_user(
                                    request,
                                    f"There is an issue in your json architecture. Please verify you file. Error {e}",
                                    level=messages.ERROR,
                                )
                                return redirect("admin:index")
                            # Process all the saving of the items (in import_assessment.py)
                            # If it fails, there is a message and a redirection to admin
                            try:
                                assessment_success, assessment_save_message = treat_and_save_dictionary_data(dict_data)
                            except (ValueError, KeyError) as e:
                                # If the import fails, the assessment created is deleted inside the same function
                                assessment_success = False
                                assessment_save_message = f"The import of the assessment failed. " \
                                                          f"Please, verify your file. Error {e}"
                            if not assessment_success:
                                self.message_user(
                                    request,
                                    assessment_save_message,
                                    level=messages.ERROR,
                                )
                                return redirect("admin:index")

                            # Update the scoring with the import file
                            if assessment_success:
                                assessment = get_last_assessment_created()  # It is the assessment just created
                                self.import_scoring(request, assessment)

                            # Process the import of the upgrade json
                            dict_upgrade_data = json.loads(decoded_upgrade_file)
                            # Verify the validity of the upgrade json and if it s ok, save it in Upgrade
                            upgrade_success, upgrade_message = check_upgrade(dict_upgrade_data)
                            if not upgrade_success:
                                self.message_user(
                                    request, upgrade_message, level=messages.ERROR,
                                )
                                return redirect("admin:index")
                            upgrade_save_success, upgrade_save_message = save_upgrade(
                                dict_upgrade_data
                            )
                            if not upgrade_save_success:
                                self.message_user(
                                    request, upgrade_save_message, level=messages.ERROR,
                                )
                                return redirect("admin:index")

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

                    # Else this is the first assessment that we are going to import so we don't need an upgrade_file
                    else:
                        # Process the import of the assessment
                        try:
                            dict_data = json.loads(decoded_assessment_file)
                        except json.JSONDecodeError as e:
                            self.message_user(
                                request,
                                f"There is an issue in your json architecture. Please verify you file. Error {e}",
                                level=messages.ERROR,
                            )
                            return redirect("admin:index")
                        # Process all the saving of the items (in import_assessment.py)
                        try:
                            (
                                assessment_success,
                                assessment_save_message,
                            ) = treat_and_save_dictionary_data(dict_data)
                        except (ValueError, KeyError) as e:
                            # todo delete the parts of the assessment created (if there are)
                            assessment_success = False
                            assessment_save_message = f"The import of the assessment failed." \
                                                      f" Please, verify your file. Error {e}"

                        if not assessment_success:
                            self.message_user(
                                request, assessment_save_message, level=messages.ERROR,
                            )
                            return redirect("admin:index")
                        else:
                            assessment = get_last_assessment_created()  # It is the assessment just created
                            self.import_scoring(request, assessment)
                            self.message_user(
                                request,
                                assessment_save_message,
                                level=messages.SUCCESS,
                            )

                # Else there is an issue with the assessment json format (which is not a json)
                else:
                    self.message_user(
                        request,
                        f"Incorrect file type: {request.FILES['assessment_json_file'].name.split('.')[1]}",
                        level=messages.ERROR,
                    )

        else:
            self.message_user(
                request,
                f"There was an error in the form {JsonUploadForm.errors}",
                level=messages.ERROR,
            )

        return redirect("admin:index")

    def import_scoring(self, request, assessment):
        """
        This function modify the scoring system created during the assessment import (or the scoring associated
        to this assessment if it already exists). It checks the json of the master_choices_weight is well
        formatted according to the assessment and then get the scoring system and replace this field to the new one
        and save the object.
        :param assessment:
        :param request:
        :return:
        """
        # Import the scoring after the import of the assessment and the upgrade table
        # The scoring has been initialized with empty values
        if request.FILES["scoring_json_file"].name.endswith("json"):
            # Handles the exception in case it is a bad json format
            decoded_scoring_file = self.decode_file(
                request, "scoring_json_file"
            )
            # Test that the scoring system has a good format
            success_scoring, message_scoring = check_and_valid_scoring_json(
                decoded_file=decoded_scoring_file, assessment=assessment
            )

            if not success_scoring:
                self.message_user(
                    request,
                    message_scoring,
                    level=messages.ERROR,
                )
                assessment.delete()
                return redirect("admin:index")
            try:
                # The scoring has been automatically created with the assessment import
                # We just set the json weight now
                scoring = ScoringSystem.objects.get(assessment=assessment)
                scoring.master_choices_weight_json = literal_eval(decoded_scoring_file)
                scoring.save()
                self.message_user(
                    request,
                    "The scoring system has been imported!",
                    level=messages.SUCCESS,
                )
            except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
                self.message_user(
                    request,
                    f"The scoring is not unique or doesn't exist "
                    f"(query {ScoringSystem.object.filter(assessment=assessment)})"
                    f" for the assessment {assessment}, error {e}",
                    level=messages.ERROR,
                )
                assessment.delete()
                return redirect("admin:index")

        # Else there is an issue with the scoring json format (which is not a json)
        else:
            assessment.delete()
            self.message_user(
                request,
                f"Incorrect file type: {request.FILES['scoring_json_file'].name.split('.')[1]}",
                level=messages.ERROR,
            )

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
                f"There was an error decoding the file:{e}",
                level=messages.ERROR,
            )
            return redirect("admin:index")
        return decoded_file

    def add_new_language_assessment(self, request, queryset):
        if len(list(queryset)) == 1:
            assessment = queryset[0]
            # TODO see for the language when upgrading
            if len(assessment.get_the_available_languages()) > 1:
                self.message_user(request, "There are already 2 languages for the assessment", messages.ERROR)
                return redirect("admin:index")
            else:
                assessment_language_tag = assessment.get_the_available_languages()[0]
            assessment_language_import = "English" if assessment_language_tag == "fr" else "French"
            context = {
                "assessment_language_tag": assessment_language_tag,
                "assessment_language_import": assessment_language_import,
                "form": ImportAssessmentNewLanguageForm(),
                "assessment": assessment,
            }
            response = render(request, "assessment/admin/import-new-language.html", context)
            return response
        else:
            self.message_user(request, "You need to select only one assessment", messages.ERROR)
            return redirect("admin:index")
    add_new_language_assessment.short_description = _("I want to import the assessment in a new language")

    def import_assessment_new_language(self, request, *args, **kwargs):
        assessment = get_object_or_404(Assessment, id=kwargs.get("id"))
        if request.method == "POST":
            form = ImportAssessmentNewLanguageForm(request.POST, request.FILES)
            if form.is_valid():
                if request.FILES["assessment_file"].name.endswith("json"):
                    decoded_assessment_file = self.decode_file(request, "assessment_file")
                    try:
                        dict_data = json.loads(decoded_assessment_file)
                    except json.JSONDecodeError as e:
                        self.message_user(
                            request,
                            f"There is an issue in your json architecture. Please verify you file. Error {e}",
                            level=messages.ERROR,
                        )
                        return redirect("admin:index")
                    # Save the assessment as new language so only the names, texts, descriptions of the objects
                    # and compare that it is valid (same format, version) than the assessment in other languages
                    try:
                        assessment_success, assessment_save_message = save_new_assessment_language(dict_data,
                                                                                                   assessment)
                    except (ValueError, KeyError) as e:
                        # If the import fails, the assessment created is deleted inside the same function
                        assessment_success = False
                        assessment_save_message = f"The saving of the new assessment language failed. " \
                                                  f"Please, verify your file. Error {e}"
                    if not assessment_success:
                        self.message_user(
                            request,
                            assessment_save_message,
                            level=messages.ERROR,
                        )
                    # Success!
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
                        f"Incorrect file type: {request.FILES['assessment_file'].name.split('.')[1]}",
                        level=messages.ERROR,
                    )
            else:
                self.message_user(
                    request,
                    f"There was an error in the form {ImportAssessmentNewLanguageForm.errors}",
                    level=messages.ERROR,
                )

        return redirect("admin:index")
