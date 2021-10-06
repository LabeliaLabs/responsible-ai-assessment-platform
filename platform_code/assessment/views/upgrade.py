import json
import logging

from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

from assessment.models import Evaluation, get_last_assessment_created
from assessment.views.utils.security_checks import can_edit_security_check
from assessment.views.utils.utils import manage_upgrade_next_url, manage_missing_language
from home.models import Organisation


logger = logging.getLogger('monitoring')


def upgradeView(request, *args, **kwargs):
    """
    This view is called when the user wants to upgrade an evaluation which is not at the latest version.
    If all the conditions are satisfied, it creates a new evaluation at the latest version based on the answers of the
    current one and it redirects to the new, on the same page the user triggered the upgrade action.
    """
    user = request.user
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist
    # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
    if not can_edit_security_check(request, organisation=organisation):
        return redirect("home:homepage")

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, organisation=organisation)
    manage_missing_language(request, evaluation)
    evaluation_version = evaluation.assessment.version
    latest_version = get_last_assessment_created().version
    data_update = {"success": False, "message": _("The operation failed. Please try again or"
                                                  " contact the site administrators")}
    if float(evaluation_version) < float(latest_version):

        try:
            new_eval = evaluation.upgrade(user=user)
            # Manage the redirection between the different pages where the user clicked to upgrade the evaluation
            url = manage_upgrade_next_url(request, new_eval, organisation, evaluation_id)
            data_update["redirection"] = url
            data_update["success"] = True
            data_update["message"] = _("Your evaluation has been upgraded."
                                       " You will be redirected to the new version.")
            logger.info(f"[upgrade] The user {request.user.email} upgrade his evaluation (id: {evaluation_id})")

        except ValueError:
            logger.warning(f"[upgrade_failed] The user {request.user.email} tried to upgrade his evaluation "
                           f"(id: {evaluation_id}) but it failed")
            messages.warning(request, _("We are sorry, the operation failed."))

    return HttpResponse(json.dumps(data_update), content_type="application/json")
