import logging

from django.contrib import messages
from django.contrib.auth.views import login_required
from django.shortcuts import redirect

from django.utils.translation import gettext as _, ngettext

from assessment.templatetags.assessment_tags import stringify_list
from home.models import Organisation

logger = logging.getLogger('monitoring')


@login_required(login_url="/login/")
def delete_user(request):
    """
    When the user wants to delete his account. First he needs to be login.
    If it s ok, we need to delete his memberships, his userresources, and the case where his is the only admin of
    an orga, the orga. As the evaluations of the orga are "models.CASCADE", the evaluations will be deleted
    automatically.
    If the user is not the only admin of the orga, we won't delete it, and we won't delete the evaluation he has
    created also because they may be useful for the other admins.

    :param request:
    :return:
    """

    user = request.user
    list_orga_user_is_admin = Organisation.get_list_organisations_where_user_as_role(user=user, role="admin")
    for orga in list_orga_user_is_admin:
        # If the user is the only admin of the organisation
        if orga.count_admin_members() == 1:
            # Delete the organisation and thus, the evaluations attached (CASCADE)
            logger.info(f"[organisation_deletion] The orga {orga.name} has been deleted with the deletion of "
                        f"the user account {user.email}")
            orga.delete()
    # UserResources is deleted on CASCADE
    # Membership is deleted on CASCADE
    logger.info(f"[account_deletion] The user {user.email} has deleted his account")
    user.delete()

    if len(list_orga_user_is_admin) == 0:
        messages.success(request, _("Your account has been deleted."))
    else:
        messages.success(request, ngettext("Your account has been deleted as well as the organisation"
                                           " %(list_organisations)s and its evaluations.",
                                           "Your account has been deleted as well as the organisations: "
                                           "%(list_organisations)s and their evaluations associated.",
                                           len(list_orga_user_is_admin)
                                           ) % {
                             'list_organisation': stringify_list(list_orga_user_is_admin)
                         }
                         )
    return redirect("home:homepage")
