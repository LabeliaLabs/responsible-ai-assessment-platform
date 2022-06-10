import logging

from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import get_object_or_404
from sentry_sdk import capture_message

from home.models import Organisation


logger = logging.getLogger('monitoring')


def membership_security_check(request, *args, **kwargs):
    """
    This function checks that the user is member of the organisation.
    :returns boolean
    """
    user = request.user
    organisation = kwargs.get("organisation", None)
    # If we don't have the organisation in the kwargs
    if organisation is None:
        organisation_id = kwargs.get("orga_id", None)
        organisation = get_object_or_404(Organisation, id=organisation_id)
    is_member = organisation.check_user_is_member(user=user)
    if not is_member:
        messages.warning(request, _("You don't have access to this content."))
        capture_message(f"[forced_url] The user {request.user.email} tried to access to the organisation "
                       f"{organisation} while not member")
    return is_member


def membership_admin_security_check(request, *args, **kwargs):
    """
    This function checks that the user is member as ADMIN of the organisation.
    :returns: boolean
    """
    user = request.user
    organisation = kwargs.get("organisation", None)
    # If we don't have the organisation in the kwargs
    if organisation is None:
        organisation_id = kwargs.get("orga_id", None)
        organisation = get_object_or_404(Organisation, id=organisation_id)
    is_member_as_admin = organisation.check_user_is_member_as_admin(user=user)
    return is_member_as_admin


def can_edit_security_check(request, *args, **kwargs):
    """
    This function checks that the user is member as ADMIN or EDIT of the organisation.
    Returns boolean True if he is, else False
    """
    user = request.user
    organisation = kwargs.get("organisation", None)
    # If we don't have the organisation in the kwargs
    if organisation is None:
        organisation_id = kwargs.get("orga_id", None)
        organisation = get_object_or_404(Organisation, id=organisation_id)
    is_member_allowed_to_edit = organisation.check_user_is_member_and_can_edit_evaluations(user=user)
    return is_member_allowed_to_edit
