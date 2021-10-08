import logging
import os

from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.contrib import messages
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.conf import settings

from assessment.models import Evaluation, Labelling
from assessment.views.utils.security_checks import membership_admin_security_check
from assessment.views.utils.utils import manage_missing_language
from home.models import Organisation, PlatformManagement

logger = logging.getLogger('monitoring')


def labellingView(request, *args, **kwargs):
    """
    This view is called when the user initiates the labelling process for an evaluation.
    The evaluation must be finished and must have a score above 60.
    The conditions fulfilled :
        - the labelling object is created and associated to the evaluation
        - an email is sent to the substra admin to inform them of the demand
        - the evaluation cannot be modified nor deleted
        - the duplication of the evaluation is possible
    """
    user = request.user
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist
    # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
    if not membership_admin_security_check(request, organisation=organisation):
        return redirect("home:homepage")

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, organisation=organisation)
    manage_missing_language(request, evaluation)
    evaluation_score = evaluation.evaluationscore_set.all().first()  # TODO improve
    if evaluation.is_finished and evaluation_score.score >= PlatformManagement.get_labelling_threshold():
        if not evaluation.has_labelling():
            Labelling.create_labelling(evaluation=evaluation)

        send_labelling_email(
            request=request,
            user=user,
            organisation=organisation,
            evaluation=evaluation,
            mail_subject=_("Initiation of the labelling process"),
            html_template="labelling/start-labelling-email.html"
        )
        evaluation.freeze_evaluation()  # Also done in create_labelling
        logger.info(f"[labelling_initialization] The user {user.email} asked "
                    f"to certificate his evaluation (id={evaluation.id})")
        messages.success(request, _("The request to label your evaluation has been sent."))
    else:  # Evaluation not finished or score not > labelling_threshold
        messages.error(request, _("You cannot start the labelling for this evaluation."))
    return redirect("home:user-profile", "labelling")


def labellingAgainView(request, *args, **kwargs):
    """
    This view is called when the user validate again his evaluation for the labelling process
    """
    user = request.user
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist
    # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
    if not membership_admin_security_check(request, organisation=organisation):
        return redirect("home:homepage")

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, organisation=organisation)
    manage_missing_language(request, evaluation)
    if not evaluation.is_finished:
        messages.warning(request, _("You need to complete the evaluation in order to submit again the labelling."))
        return redirect("home:user-profile", "labelling")

    if not evaluation.has_labelling():
        messages.warning(request, _("We are sorry, the operation failed."))
        logger.warning(f"[labelling_again_failed] The user {request.user.email} tried to submit again the labelling "
                       f"process for the evaluation (id: {evaluation_id}) but it failed - no labelling object.")
    else:
        labelling = evaluation.get_labelling()
        labelling.submit_again()  # Increment the counter, set the status to "progress" and freeze evaluation
        send_labelling_email(
            request=request,
            user=user,
            organisation=organisation,
            evaluation=evaluation,
            mail_subject=_("Submit the labelling again after modifications"),
            html_template="labelling/labelling-again-email.html"
        )
        messages.success(request, _("The request has been sent."))
    return redirect("home:user-profile", "labelling")


def labellingJustification(request, *args, **kwargs):
    """
    View called when an admin user asks the user to modify its evaluation in order to
    obtain the label.
    """
    user = request.user
    if not user.is_admin:
        messages.warning(request, _("This action is for admin only."))
        return redirect("home:homepage")
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(Organisation, id=organisation_id)

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, organisation=organisation)
    evaluation.labelling.set_justification_required()
    messages.success(request, _("The status of the labelling has been modified."))
    return redirect('home:admin-dashboard', 'labelling')


def labellingEnd(request, *args, **kwargs):
    """
    View called when an admin user rejects/validates a labelling.
    """
    user = request.user
    if not user.is_admin:
        messages.warning(request, _("This action is for admin only."))
        return redirect("home:homepage")
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id, organisation=organisation)
    status = kwargs.get('status')
    if not status or (status != "rejection" and status != "validation"):
        messages.warning(
            request,
            _("There is a technical issue with the action. Please contact the technical support.")
        )
    else:
        evaluation.labelling.set_final_status(status)
        messages.success(
            request,
            _(f"The labelling has well been {'rejected' if status == 'rejection' else 'validated'}.")
        )
    return redirect('home:admin-dashboard', 'labelling')


def send_labelling_email(request, user, organisation, evaluation, mail_subject, html_template):
    """
    Send a email to substra admin to inform them that the
    user asked to certificate his evaluation
    """
    current_site = get_current_site(request)
    message = render_to_string(f'assessment/{html_template}', {
        'user': user,
        'domain': current_site.domain,
        'protocol': "http" if settings.DEBUG else "https",
        'evaluation': evaluation,
        'organisation': organisation,
    })
    to_email = os.environ.get("EMAIL_USER")
    email = EmailMessage(
        mail_subject, message, to=[to_email]
    )
    email.send()
