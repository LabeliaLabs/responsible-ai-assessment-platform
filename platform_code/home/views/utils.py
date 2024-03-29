import logging

from assessment.models import (
    Assessment,
    ElementChangeLog,
    MasterEvaluationElement,
    MasterSection,
    get_last_assessment_created,
)
from django.utils.translation import gettext as _
from home.models import Organisation, UserResources
from sentry_sdk import capture_message

logger = logging.getLogger("monitoring")


def organisation_required_message(context):
    """
    I do not use the django method to display messages as the front is to 'ugly' and I have an easier way to do this
    as long as there is only one message to display
    :param context:
    :return:
    """
    context["message"] = {
        "alert-warning": _(
            "You first need to create your organisation before creating your evaluation."
        )
    }


def organisation_creation(request, form):
    """
    This function is used to create an organisation from a valid form.
    This is used in the CBV

    :param form: OrganisationCreationForm
    :param request: request POST

    :return: organisation
    """
    user = request.user
    name = form.cleaned_data.get("name")
    size = form.cleaned_data.get("size")
    country = form.cleaned_data.get("country")
    sector = form.cleaned_data.get("sector")
    # This method handles the fact that the membership is created for this orga as admin
    organisation = Organisation.create_organisation(
        name=name,
        size=size,
        country=country,
        sector=sector,
        created_by=user,
    )
    logger.info(
        f"[organisation_creation] A new organisation {organisation.name} has been created by "
        f"the user {user.email}"
    )
    return organisation


def manage_user_resource(request):
    """
    This function is used to check that the user has only one user_resource and create one if he doesn't have.
    Used in ProfileView

    :returns: user_resources
    """
    user = request.user
    user_resources = UserResources.objects.filter(user=user)
    if len(user_resources) == 1:
        return user_resources[0]
    # Case the user resource does not exist, which should not happen
    # but it does when you create super user with the shell
    elif len(user_resources) == 0:
        UserResources.create_user_resources(
            user=user
        )  # create user_resources so the user can access resources
        user_resources = UserResources.objects.get(user=user)
        return user_resources
    else:
        capture_message(
            f"[multiple_user_resources] The user {user.email} has multiple user resources, auto-cleaning"
        )
        while UserResources.objects.filter(user=user).count() > 1:
            UserResources.objects.filter(user=user)[-1].delete()
        return UserResources.objects.get(user=user)


def add_last_version_last_assessment_dictionary(dictionary):
    """
    Add the last assessment and the last version to the dictionary if they exist, else empty list for last_version
    This is used in the CBV, ProfileView for example with self.context as dictionary

    :param dictionary: dict
    :returns: dict
    """
    if isinstance(dictionary, dict):
        if get_last_assessment_created():
            dictionary[
                "last_version"
            ] = get_last_assessment_created().version  # get last version
            dictionary["last_assessment"] = get_last_assessment_created()
        else:
            dictionary["last_version"] = []
    return dictionary


def add_resources_dictionary(dictionary, user, user_resources):
    """
    Add the resources liked and the resources in the dictionary

    :param user:
    :param dictionary:
    :param user_resources:

    :return: the dictionary with new keys "resources" and "resources_liked"
    """
    if isinstance(dictionary, dict):
        query_resources_dict = user_resources.resources.all()
        dictionary["resources"] = query_resources_dict
        dictionary["resources_liked"] = user.userresources.resources.all()
    return dictionary


def get_all_change_logs():
    """
    Return a dictionary of the following structure:
    {
    "assessment_name.assessment_version":{
         "master section name": {
             "master evaluation element name": {
                  {
                    "edito":"bla bla",
                    "pastille":"New",
                  }
                  ...
             }
             ...
         }
         ...
      }
    ....
    }
    These change logs will be displayed on ProfileView
    """
    assessments = Assessment.objects.all()
    change_logs_dict = {}
    if assessments:
        for assessment in assessments:
            # check if there are any change logs for this version
            change_logs = ElementChangeLog.objects.filter(assessment=assessment)
            if change_logs:
                change_logs_dict[assessment] = {}
                master_sections = MasterSection.objects.filter(assessment=assessment)
                for master_section in master_sections:
                    change_logs_dict[assessment][master_section] = {}
                    master_evaluation_elements = MasterEvaluationElement.objects.filter(
                        master_section=master_section
                    )
                    for master_evaluation_element in master_evaluation_elements:
                        try:
                            change_log = ElementChangeLog.objects.get(
                                eval_element_numbering=master_evaluation_element.get_numbering(),
                                previous_assessment=assessment.previous_assessment,
                                assessment=assessment,
                            )
                        except (
                            ElementChangeLog.DoesNotExist,
                            ElementChangeLog.MultipleObjectsReturned,
                        ):
                            change_log = None

                        if change_log is not None:
                            if (
                                change_log.pastille != "Unchanged"
                                and change_log.pastille != "Inchangé"
                            ):
                                change_logs_dict[assessment][master_section][
                                    master_evaluation_element
                                ] = {}
                                change_logs_dict[assessment][master_section][
                                    master_evaluation_element
                                ] = change_log
                    if not change_logs_dict[assessment][master_section]:
                        # delete sections that contain unchanged elements only
                        del change_logs_dict[assessment][master_section]

    return change_logs_dict
