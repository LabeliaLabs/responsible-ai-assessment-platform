import logging
import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from sentry_sdk import capture_message

from assessment.models import Evaluation
from assessment.views.utils.security_checks import membership_security_check, can_edit_security_check
from assessment.views.utils.utils import manage_missing_language
from home.models import Organisation


logger = logging.getLogger('monitoring')


def duplicateView(request, *args, **kwargs):
    """
    This view is used to duplicate an evaluation. This process creates a new evaluation with
    the same answers than the original.
    This is used when an evaluation cannot be modified due to labelling process ongoing.
    The new evaluation can be modified.
    """

    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist
    # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
    if not membership_security_check(request, organisation=organisation):
        return redirect("home:homepage")

    # Check if the user is an admin/editor member of the orga, if not, return to the same page
    if not can_edit_security_check(request, organisation=organisation):
        messages.warning(request, _("You don't have the right to do this action."))
        return redirect("home:user-profile")

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, organisation=organisation)
    manage_missing_language(request, evaluation)
    data_update = {}
    if not evaluation.has_labelling():
        messages.warning(request, _("You can only duplicate evaluations with labelling."))
        return redirect("home:user-profile")
    try:
        new_evaluation = evaluation.duplicate_evaluation()
        # Manage the redirection between the different pages where the user clicked to upgrade the evaluation
        logger.info(f"[duplication] The user {request.user.email} has duplicated his evaluation (id: {evaluation_id}),"
                    f" new evaluation (id: {new_evaluation.id})")
        data_update["success"] = True
        messages.success(
            request, _(f"Your evaluation has been duplicated. The duplicate is {str(new_evaluation)}")
        )

    except ValueError:
        capture_message(f"[duplication_failed] The user {request.user.email} tried to duplicate his evaluation "
                       f"(id: {evaluation_id}) but it failed")
        data_update["success"] = False
        data_update["message"] = _("We are sorry, the operation failed.")
        messages.warning(request, _("We are sorry, the operation failed."))

    return HttpResponse(json.dumps(data_update), content_type="application/json")
