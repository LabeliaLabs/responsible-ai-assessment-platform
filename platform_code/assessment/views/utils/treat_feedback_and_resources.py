import json
import logging
import markdown
import requests
from datetime import datetime, timedelta

from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.conf import settings

from assessment.forms import (
    ElementFeedbackForm,
    SectionFeedbackForm,
    element_feedback_list,
    section_feedback_list,
)
from assessment.models import ExternalLink, EvaluationElement, Section
from assessment.utils import get_client_ip
from assessment.views.utils.error_handler import error_500_view_handler

logger = logging.getLogger('monitoring')
private_token = settings.PRIVATE_TOKEN
project_id = str(settings.PROJECT_ID)


def treat_resources(request):
    """
    This function treats the POST methods when the user likes or unlikes resources, both from the evaluations
    and from his profile/resource page. It receives a resource id (we check it s really a resource id) and if
    the resource id is already in the resource m2m field of the user resource, so the user unliked it and we remove it
    from the field. Otherway, the user liked it and the resource is added to the field.
    """
    resource_id = request.POST.dict().get("resource_id")
    data_update = {"success": False, "no_resource_liked": False}
    try:
        resource = ExternalLink.objects.get(id=resource_id)
    except KeyError as e:
        logger.error(f"[resource_error] The resource id {resource_id} from the post of "
                     f"the user {request.user.email} is not a resource")
        error_500_view_handler(request, exception=e)

    # object user_resources
    user_r = request.user.userresources
    # queryset of all the resources the user liked
    user_resources = user_r.resources.all()

    # Case the resource is already liked so the user wants to unlike it : we remove it from the m2m field resources
    if resource in user_resources:
        # Remove the resource, no issue if the resource is not in the filed
        user_r.resources.remove(resource)
        user_r.save()
        data_update["success"] = True
        data_update["like"] = False
        if len(list(user_r.resources.all())) == 0:
            data_update["no_resource_liked"] = True
    # Case the resource is not liked so the user likes it and we add the resource to the m2m field resources
    elif resource not in user_resources:
        # Add the resource to the field, do not create duplicate if it is already
        user_r.resources.add(resource)
        user_r.save()
        data_update["success"] = True
        data_update["like"] = True
        # We need to add these data when the user likes a resource from the resource list in the resource page to add
        # A new line in the favorite resources. I ve chosen to not add the possibility of removing it in this list (no
        # Form, cf javascript like.js : like function)
        data_update["resource_text"] = markdown.markdown(
            "[" + resource.type + "] - " + resource.text
        )

    return HttpResponse(json.dumps(data_update), content_type="application/json")


def treat_feedback(request, *args, **kwargs):
    """
    This functions treats the ajax post when the user submit a feedback for an evaluation element.
    It create a POST request to the framagit API in order to create the issue
    :param request:
    :return:
    """
    evaluation = kwargs.get("evaluation")  # Evaluation or None
    data_update = {
        "success": False,
        "message": _(
            "We are sorry but the message has not been sent. "
            "Try again or contact the Substra team through another channel."
        ),
    }

    if "element" in args:
        feedback = "element_feedback"
        form = ElementFeedbackForm(request.POST)
    elif "section" in args:
        feedback = "section_feedback"
        form = SectionFeedbackForm(request.POST)
    else:
        logger.error("[feedback_error] There is a feedback not for the element nor the section")
        form = None
        error_500_view_handler(request, exception=None)

    if form and form.is_valid():
        # If the function is called by a post for the element feedback
        if feedback == "element_feedback":
            feedback_element_type = form.cleaned_data.get("element_feedback_type")
            object_id = request.POST.dict().get("element_id")
            feedback_text = next(
                elem[1]
                for elem in element_feedback_list
                if feedback_element_type in elem
            )
            try:
                feedback_object = EvaluationElement.objects.get(id=object_id)
                master_id = feedback_object.master_evaluation_element.id
                object_type = "master_section"
            except KeyError as e:
                logger.error(f"[feedback_error] The element id {object_id} is not an id of an element in the database,"
                             f" from the feedback post")
                error_500_view_handler(request, exception=e)

            if feedback_object and evaluation:
                # If the user forced the html, and tried to sent element feedback for an evaluation element which
                # does not belong to the evaluation
                if feedback_object not in evaluation.get_list_all_elements():
                    logger.warning(f"[html_forced] The user {request.user.email}, with IP address "
                                   f"{get_client_ip(request)} modified the html to do "
                                   f"a POST request {request.POST} for an element feedback on an evaluation element "
                                   f"which does not belong to the current evaluation (id {evaluation.id})")
                    data_update["message"] = _("An error occurred. The feedback does not have been sent.")
                    return HttpResponse(json.dumps(data_update), content_type="application/json")

        # If the function is called by a post in the section feedback
        else:
            feedback_section_type = form.cleaned_data.get("section_feedback_type")
            object_id = request.POST.dict().get("section_id")
            feedback_text = next(
                elem[1]
                for elem in section_feedback_list
                if feedback_section_type in elem
            )
            try:
                feedback_object = Section.objects.get(id=object_id)
                master_id = feedback_object.master_section.id
                object_type = "master_evaluation_element"
            except KeyError as e:
                logger.error(f"[feedback_error] The section id {object_id} is not an id of a section in the database,"
                             f" from the feedback post")
                error_500_view_handler(request, exception=e)
            # If the user forced the html, and tried to sent section feedback for a section which does not
            # belong to the evaluation
            if feedback_object and evaluation:
                if feedback_object not in evaluation.section_set.all():
                    logger.warning(f"[html_forced] The user {request.user.email}, with IP address "
                                   f"{get_client_ip(request)} modified the html to do "
                                   f"a POST request {request.POST} for a section feedback on a section which "
                                   f"does not belong to the current evaluation (id {evaluation.id})")
                    data_update["message"] = _("An error occurred. The feedback does not have been sent.")
                    return HttpResponse(json.dumps(data_update), content_type="application/json")
        # Process variables to sent to the framagit API to create the issue
        text = form.cleaned_data.get("text")
        user = request.user
        user_email = user.get_email()
        user_name = user.get_full_name()
        # Create the request to the framagit/gitlab API
        url = "https://framagit.org/api/v4/projects/" + project_id + "/issues"
        headers = {"PRIVATE-TOKEN": private_token}
        data = {
            "title": "Feedback sur "
                     + str(feedback_object)
                     + " ("
                     + object_type
                     + " id="
                     + str(master_id)
                     + ")",
            "labels": "feedback",
            "description": "["
                           + str(feedback_text)
                           + "] de "
                           + user_name
                           + ", "
                           + user_email
                           + " sur l'objet "
                           + str(feedback_object)
                           + ".\n\n Message de l'utilisateur : "
                           + text,
        }

        # If the user doesn't spam the feedback, ie he doesn't send more than max_feedback (19)
        # since delta_days (2 days)
        if not is_user_spam_feedback(url, headers, user, delta_days=1, max_feedback=19):
            try:
                response = requests.post(url, headers=headers, data=data)
                if response.status_code == 200 or 201:  # if 200 or 201 for created
                    data_update["success"] = True
                    data_update["message"] = _(
                        "Thank you for your feedback, it helps us a lot!"
                        " We will take it into consideration as soon as possible."
                    )
                    logger.info(f"[feedback] The user {request.user.email} sent a feedback")
                else:
                    logger.error(f"[feedback_error] There is an issue with the feedback API, the request has "
                                 f"the response {response.json()} and a status code {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"[feedback_error] There is an issue with the feedback API, error {e}")
        else:
            logger.error(f"[feedback_error] The user {user.email} spams the feedback feature !")
            data_update["message"] = _("Please, do not spam the feature. If your are not, contact the support service!")

    return HttpResponse(json.dumps(data_update), content_type="application/json")


def is_user_spam_feedback(url, headers, user, delta_days, max_feedback):
    """
    This function aims to check, when a user post a feedback if he isn't spaming the features. The limitation is
    arbitrary set to max_feedback since the delta in days (delta_days (integer))
    :param user: user
    :param delta_days: integer, the number of days to check before
    :param url:  string, url of framagit project
    :param headers: dictionary, headers with private token
    :param max_feedback: maximum number of feedback sent, integer
    :return:
    """
    date_now = datetime.now()
    delta_time = date_now - timedelta(days=delta_days)
    data = {"labels": "feedback", "created_after": delta_time}
    response = requests.get(url, headers=headers, data=data)
    # Always the last 20 issues created
    issues_list = response.json()
    count = 0
    if len(issues_list) > 0:
        i = 0
        while i < len(issues_list) and count <= max_feedback:
            issue = issues_list[i]
            # The user email is not in the author dictionary but in the description, so we check it
            description = issue["description"]
            user_email = user.get_email()
            if user_email in description:
                # so the user created the issue, now we check the date
                created_at = issue["created_at"].split("T")[0]
                # convert into datetime format
                formatted_created_at = datetime.strptime(created_at, "%Y-%m-%d")
                # If the issue has been created between the delta days and now, we count this issue
                if formatted_created_at > delta_time:
                    count += 1
            i += 1
    return count > max_feedback
