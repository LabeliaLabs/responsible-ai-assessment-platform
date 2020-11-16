import json
from ast import literal_eval

from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import TO_FIELD_VAR, IS_POPUP_VAR
from django.contrib.admin.utils import flatten_fieldsets, unquote
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist, MultipleObjectsReturned
from django.forms import widgets, all_valid
from django.shortcuts import redirect
from django.urls import path  # Used to import Json
from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext as _

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
    EvaluationScore,
)

from assessment.scoring import check_and_valid_scoring_json


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
admin.site.register(Upgrade)
admin.site.register(EvaluationScore)

# Import json Assessment #


class JsonUploadAssessmentAdmin(admin.ModelAdmin):
    """
    This class defines the assessment json import, the choice scoring json import as well as the upgrade_json import.
    From the assessment json file, we create all the objects it contains.
    If there are more than one assessment in the database, an upgrade json must be provided (refer to the doc
    "multiple_version.md" to see the format). From this upgrade json, the table Upgrade is populated.
    """

    # TODO refactor a little bit this function
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
                                return redirect("admin/")
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
                                return redirect("admin/")

                            # Update the scoring with the import file
                            if assessment_success:
                                assessment = get_last_assessment_created()  # It is the assessment just created
                                self.import_scoring(request, assessment)

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
                                    request, upgrade_save_message, level=messages.ERROR,
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
                            return redirect("admin/")
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
                            return redirect("admin/")
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

        return redirect("admin/")

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
                return redirect("admin/")
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
                return redirect("admin/")

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
            return redirect("admin/")
        return decoded_file


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

    def _changeform_view(self, request, object_id, form_url, extra_context):
        """
        Just add a try/except when saving the form in case there are issues with the scoring file
        :param request:
        :param object_id:
        :param form_url:
        :param extra_context:
        :return:
        """
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        model = self.model
        opts = model._meta

        if request.method == 'POST' and '_saveasnew' in request.POST:
            object_id = None

        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            if request.method == 'POST':
                if not self.has_change_permission(request, obj):
                    raise PermissionDenied
            else:
                if not self.has_view_or_change_permission(request, obj):
                    raise PermissionDenied

            if obj is None:
                return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        ModelForm = self.get_form(request, obj, change=not add)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            form_validated = form.is_valid()
            if form_validated:
                try:
                    new_object = self.save_form(request, form, change=not add)
                except (ValidationError, MultipleObjectsReturned, ObjectDoesNotExist) as e:
                    self.message_user(
                        request,
                        f"There was an error during the saving of the scoring: {e}",
                        level=messages.ERROR,
                    )
                    return redirect("admin/")
            else:
                new_object = form.instance
            formsets, inline_instances = self._create_formsets(request, new_object, change=not add)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, not add)
                self.save_related(request, form, formsets, not add)
                change_message = self.construct_change_message(request, form, formsets, add)
                if add:
                    self.log_addition(request, new_object, change_message)
                    return self.response_add(request, new_object)
                else:
                    self.log_change(request, new_object, change_message)
                    return self.response_change(request, new_object)
            else:
                form_validated = False
        else:
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(request, form.instance, change=False)
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(request, obj, change=True)

        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            self.get_prepopulated_fields(request, obj) if add or self.has_change_permission(request, obj) else {},
            readonly_fields,
            model_admin=self)
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        if add:
            title = _('Add %s')
        elif self.has_change_permission(request, obj):
            title = _('Change %s')
        else:
            title = _('View %s')
        context = {
            **self.admin_site.each_context(request),
            'title': title % opts.verbose_name,
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            'to_field': to_field,
            'media': media,
            'inline_admin_formsets': inline_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'preserved_filters': self.get_preserved_filters(request),
        }

        # Hide the "Save" and "Save and continue" buttons if "Save as New" was
        # previously chosen to prevent the interface from getting confusing.
        if request.method == 'POST' and not form_validated and "_saveasnew" in request.POST:
            context['show_save'] = False
            context['show_save_and_continue'] = False
            # Use the change template instead of the add template.
            add = False

        context.update(extra_context or {})

        return self.render_change_form(request, context, add=add, change=not add, obj=obj, form_url=form_url)


admin.site.register(ScoringSystem, ScoringAdmin)
