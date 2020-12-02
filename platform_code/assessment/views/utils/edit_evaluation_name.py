import json
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from assessment.utils import get_client_ip
from assessment.forms import EvaluationForm
from assessment.models import Evaluation

logger = logging.getLogger('monitoring')


def treat_evaluation_name_edition(request):
    """
    This function is used in the ProfileView and in EvaluationView to edit the name of the evaluation

    :param request: request

    :returns: response ajax (json)
    """
    user = request.user
    data_update = {"message": _("An error occurred."), "success": False}
    form = EvaluationForm(request.POST)
    if form.is_valid():
        name = form.cleaned_data.get("name")
        evaluation_id = int(request.POST.dict().get("evaluation_id"))
        evaluation = get_object_or_404(Evaluation, id=evaluation_id)  # Check the organisation below
        # If the evaluation get by the POST is not one where user can edit (so user modified html)
        if evaluation.organisation not in user.get_list_organisations_user_can_edit():
            logger.warning(f"[html_forced] The user {user.email}, with IP address {get_client_ip(request)}"
                           f" tried to modify the name of an evaluation"
                           f" (id {evaluation_id} he should not be able to edit")
            data_update["message"] = _("You cannot edit this evaluation.")
        else:
            evaluation.name = name
            evaluation.save()
            data_update["success"] = True
            data_update["message"] = _("The evaluation's name has been changed.")
            logger.info(f"[evaluation_name_changed] The user {request.user.email} changed the named of the "
                        f"evaluation (id: {evaluation_id})")
    return HttpResponse(json.dumps(data_update), content_type="application/json")
