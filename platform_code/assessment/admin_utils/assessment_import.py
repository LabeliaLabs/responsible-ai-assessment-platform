import json
from ast import literal_eval

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import redirect
from django.urls import path  # Used to import Json

from assessment.forms import JsonUploadForm
from assessment.import_assessment import ImportAssessment, check_upgrade, save_upgrade

from assessment.models import (
    ScoringSystem,
    get_last_assessment_created,
)
from assessment.scoring import check_and_valid_scoring_json


class JsonUploadAssessmentAdmin(admin.ModelAdmin):
    """
    This class defines the assessment json import, the choice scoring json import as well as the upgrade_json import.
    From the assessment json file, we create all the objects it contains.
    If there are more than one assessment in the database, an upgrade json must be provided (refer to the doc
    "multiple_version.md" to see the format). From this upgrade json, the table Upgrade is populated.
    """
    change_list_template = "assessment/admin/import-json.html"

    list_display = (
        "name",
        "version",
        "previous_assessment",
        "created_at",
        "get_number_evaluations"
    )

    @admin.display(description="Number of evaluations")
    def get_number_evaluations(self, obj):
        return obj.evaluations.all().count()

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

    def has_add_permission(self, request):
        return False

    def upload_json(self, request):
        if request.method == "POST":
            form = JsonUploadForm(request.POST, request.FILES)
            # There are the assessment and scoring files
            if form.is_valid():
                if request.FILES["assessment_json_file"].name.endswith("json") and \
                        request.FILES["scoring_json_file"].name.endswith("json"):
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
                            import_assessment = ImportAssessment(dict_data)
                            assessment_success = import_assessment.success
                            assessment_save_message = import_assessment.message
                            if not assessment_success:
                                self.message_user(
                                    request,
                                    assessment_save_message,
                                    level=messages.ERROR,
                                )
                                return redirect("admin:index")

                            # Update the scoring with the import file
                            if assessment_success:
                                assessment = import_assessment.assessment  # It is the assessment just created
                                self.import_scoring(request, assessment)

                            # Process the import of the upgrade json
                            dict_upgrade_data = json.loads(decoded_upgrade_file)
                            # Verify the validity of the upgrade json and if it s ok, save it in Upgrade
                            upgrade_success, upgrade_message = check_upgrade(dict_upgrade_data)
                            if not upgrade_success:
                                upgrade_message = upgrade_message + \
                                    " \n Due to this failure, the assessment and the scoring have been deleted. "
                                self.message_user(
                                    request, upgrade_message, level=messages.ERROR,
                                )
                                # if the upgade table is not valid then delete the assessment
                                # and the scoring from the DB
                                assessment.delete()
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

                        import_assessment = ImportAssessment(dict_data)
                        assessment_success = import_assessment.success
                        assessment_save_message = import_assessment.message

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
                        f"Incorrect file type, one is not a json: "
                        f"assessment: {request.FILES['assessment_json_file'].name.split('.')[1]}, "
                        f"scoring: {request.FILES['scoring_json_file'].name.split('.')[1]}",
                        level=messages.ERROR,
                    )
            # Form not valid
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
