import logging

from django.utils.translation import gettext as _

from home.models import Organisation, UserResources
from assessment.models import get_last_assessment_created

logger = logging.getLogger('monitoring')


def manage_message_login_page(request):
    """
    This function manages the messages displayed to the user in the login page
    I have chosen to not use the Django messages process (messages.add_message) as it doesn't work properly
    :param request:
    :return:
    """
    previous_url = request.META.get("HTTP_REFERER")
    # Case it s a redirection because the user wanted to access content where as he is not login
    if previous_url is None:
        message = {
            "alert-danger": _("You must be connected to access this content.")
        }
        return message  # break the function
    # Case the user failed to provide a good combination of email and password
    elif "/login/" in previous_url:
        message = {
            "alert-warning": _("The attempt to connect with this combination email/password failed. Please try again!")
        }

    # When signup is the previous page, the user has clicked on connexion button in the navbar after the login popin
    # process
    # Case "/signup/" in previous_url
    else:
        message = {
            " alert-info": _("Please, enter your email and your password to login to your account.\n "
                             "If you don't have an account, click on the \"I haven't an account\" button.")
        }
    return message


def organisation_required_message(context):
    """
    I do not use the django method to display messages as the front is to 'ugly' and I have an easier way to do this
    as long as there is only one message to display
    :param context:
    :return:
    """
    context["message"] = {
        "alert-warning": _("You first need to create your organisation before creating your evaluation.")
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
        name=name, size=size, country=country, sector=sector, created_by=user,
    )
    logger.info(f"[organisation_creation] A new organisation {organisation.name} has been created by "
                f"the user {user.email}")
    return organisation


def manage_user_resource(request):
    """
    This function is used to check that the user has only one user_resource and create one if he doesn't have.
    Used in ProfileView

    :returns: user_resources
    """
    user = request.user
    if len(UserResources.objects.filter(user=user)) == 1:
        user_resources = UserResources.objects.get(user=user)
    # Case the user resource does not exist, which should not happen
    # but it does when you create super user with the shell
    elif len(UserResources.objects.filter(user=user)) == 0:
        UserResources.create_user_resources(user=user)  # create user_resources so the user can access resources
        user_resources = UserResources.objects.get(user=user)
    else:
        logger.error(f"[multiple_user_resources] The user {user.email} has multiple user resources")
        user_resources = None
    return user_resources


def add_last_version_last_assessment_dictionary(dictionary):
    """
    Add the last assessment and the last version to the dictionary if they exist, else empty list for last_version
    This is used in the CBV, ProfileView for example with self.context as dictionary

    :param dictionary: dict
    :returns: dict
    """
    if isinstance(dictionary, dict):
        if get_last_assessment_created():
            dictionary["last_version"] = get_last_assessment_created().version  # get last version
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
