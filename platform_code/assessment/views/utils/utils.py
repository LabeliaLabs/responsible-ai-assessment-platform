import json
import logging

import plotly.graph_objects as go
import plotly.offline as opy
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import gettext as _, activate, get_language_from_request

from assessment.forms import ChoiceForm, ResultsForm
from assessment.models import EvaluationScore, Evaluation, get_last_assessment_created, Assessment, \
    EvaluationElement
from assessment.views.utils.error_handler import error_500_view_handler

LANGUAGE_QUERY_PARAMETER = 'language'
logger = logging.getLogger('monitoring')


def set_form_for_sections(section_query):
    """
    Create a dictionary where keys are evaluation_elements and values are forms (ChoiceForm) for the evaluation element
    The forms is made up of a radio or checkbox and a textfield for the notes
    The dictionary dic_form is used as value for the variable 'context' and will be called in the template
    :param section_query: query of all the sections of the evaluation
    :return: dic_form, evaluation_elements as keys and choice_form as values
    """
    dic_form = {}
    for section in section_query:
        for evaluation_element in section.evaluationelement_set.all():
            dic_form[evaluation_element] = ChoiceForm(
                evaluation_element=evaluation_element,
                prefix=evaluation_element.id,
            )
    return dic_form


def set_form_for_results(evaluation):
    """
    Create a dictionary where keys are evaluation_elements and values are forms (ResultsForm) for the evaluation element
    The forms is made up of a radio or checkbox and a textfield for the notes
    The form is entirely disabled
    :param evaluation
    :return: dic_form, evaluation_elements as keys and results_form as values
    """
    dic_form = {}
    for section in evaluation.section_set.all().order_by("master_section__order_id"):
        for evaluation_element in section.evaluationelement_set.all().order_by(
                "master_evaluation_element__order_id"
        ):
            dic_form[evaluation_element] = ResultsForm(
                evaluation_element=evaluation_element,
                prefix=evaluation_element.id,
            )
    return dic_form


def manage_evaluation_score(request, evaluation_list):
    """
    This function is used in Results to manage the evaluation score
    It get the object evaluation score and if needed, calculates and set the score

    :params evaluation_list: list of evaluation

    :returns: dictionary or None, dic with evaluation id as keys (int) and evaluation score as values
    """

    evaluation_score_dic = {}
    for evaluation in evaluation_list:
        try:
            evaluation_score = EvaluationScore.objects.get(evaluation=evaluation)
            # If the evaluation has changed or is finished for the first time, the score need to be set
            if evaluation_score.need_to_calculate:
                # This calculates the score and other parameters. The field need_to_calculate is set to False
                evaluation_score.process_score_calculation()
            evaluation_score_dic[evaluation.id] = evaluation_score.score
        except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError) as e:
            logger.warning(f"[evaluation_score_error] The query to return the evaluation score for the evaluation "
                           f"{evaluation.id} failed, error {e}")
            messages.warning(request, _("An error occurred."))
            evaluation_score_dic[evaluation.id] = None

    return evaluation_score_dic


def manage_evaluation_max_points(request, evaluation_list):
    """
    This function is used to set the evaluation max points if needed (after the scoring has been modified)
    It returns boolean, True if the operation succeeded, else False
    :param request:
    :param evaluation_list: list of evaluations
    :return: Boolean
    """
    success = True
    for evaluation in evaluation_list:
        try:
            evaluation_score = EvaluationScore.objects.get(evaluation=evaluation)
            if evaluation_score.need_to_set_max_points:
                evaluation_score.calculate_max_points()
        except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError) as e:
            logger.warning(f"[evaluation_score_error] The query to return the evaluation score for the evaluation "
                           f"(id {evaluation.id}) failed, error {e}, request {request}")
            messages.warning(request, _("An error occurred with the score calculation."))
            success = False
    return success


def manage_upgrade_next_url(request, new_eval, organisation, evaluation_id, *args, **kwargs):
    """
    This function is in the upgrade view function to redirect the user to the appropriate url after the upgrade.
    The purpose is to redirect to the same page before the action, the new evaluation.
    """
    previous_url = request.META.get("HTTP_REFERER")
    # If the new version is finished, we redirect to the results in any case
    if new_eval.is_finished:
        url = redirect("assessment:results", organisation.id, new_eval.slug, new_eval.pk)
        messages.success(request, _("Your evaluation has been upgraded! You have been redirected to it. "), )
    # We do not redirect to the results as the evaluation is not finished so we need to know which page
    else:
        if "/section/" in previous_url and not new_eval.is_finished:
            # url = redirect("assessment:section", organisation.id, new_eval.slug, new_eval.pk)
            messages.success(request, _("Your evaluation has been upgraded! You have been redirected to it."), )
            url = redirect("assessment:evaluation", organisation.id, new_eval.slug, new_eval.pk)
        elif "/results/" in previous_url and not new_eval.is_finished:
            url = redirect("assessment:evaluation", organisation.id, new_eval.slug, new_eval.pk)
            messages.success(
                request,
                _(
                    "Your evaluation has been upgraded! You have been redirected to it. "
                    "You have to complete the new items before the validation."
                ),
            )
        elif "/profile/" in previous_url and not new_eval.is_finished:
            url = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
            messages.success(request, _("Your evaluation has been upgraded!"))
        elif "organisation" in previous_url and not str(evaluation_id) in previous_url and not new_eval.is_finished:
            url = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
            messages.success(request, _("Your evaluation has been upgraded!"))
        # Case "else" when it is the evaluation page
        else:
            url = redirect("assessment:evaluation", organisation.id, new_eval.slug, new_eval.pk)
            messages.success(request, _("Your evaluation has been upgraded! You have been redirected to it."), )

    return url.url


def treat_evaluation_creation_valid_form(form, organisation, user):
    """
    This function is used in the POST of CBV (SummaryView, EvaluationCreation)
    to create an evaluation from the form of the POST.

    :param form: EvaluationForm or EvaluationMutliOrgaForm
    :param organisation: organisation
    :param user: user

    :returns: redirection to the url
    """
    name = form.cleaned_data.get("name")
    # Store the last evaluation version before the evaluation creation
    last_version_in_organisation = organisation.get_last_assessment_version()

    eval = Evaluation.create_evaluation(
        name=name,
        assessment=get_last_assessment_created(),
        organisation=organisation,
        user=user,
    )
    eval.create_evaluation_body()
    logger.info(f"[evaluation_creation] The user {user.email} created an evaluation {eval.name} in the organisation "
                f"{organisation.name}")
    # Check if we need to fetch the evaluation
    if last_version_in_organisation and last_version_in_organisation < float(get_last_assessment_created().version):
        origin_assessment = get_object_or_404(Assessment, version=str(last_version_in_organisation))
        eval.fetch_the_evaluation(origin_assessment=origin_assessment)

    # redirect to a new URL:
    return redirect("assessment:evaluation", organisation.id, eval.slug, eval.pk)


def create_radar_chart(object_list, math_expression, text_expression, hovertext_expression):
    """
    This function creates the radar chart of the object list, with the value coming from the object evaluated
    with the math expression (lambda function) and the text from the text expression (lambda function).
    If the math_expression and the text_expression are not lambda functions, it returns None

    :param object_list: list of objects (section)
    :param math_expression: lambda expression
    :param text_expression: lambda expression
    :param hovertext_expression: lambda expression
    """
    if math_expression.__name__ == "<lambda>" and text_expression.__name__ == "<lambda>":
        fig = go.Figure(data=go.Scatterpolar(
            # r is the radius, the first value is added at the end to loop the trace
            r=[math_expression(obj) for obj in object_list] + [math_expression(object_list[0])],
            # theta is the label
            theta=[text_expression(obj) for obj in object_list] + [text_expression(object_list[0])],
            fill='toself',
            hoverinfo="text",
            text=[hovertext_expression(obj) for obj in object_list] + [hovertext_expression(object_list[0])]
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickmode="array",
                    tickvals=[0, 20, 40, 60, 80, 100],
                    ticktext=["0%", "20%", "40%", "60%", "80%", "100%"],
                    ticks="outside",
                    angle=90
                ),
            ),
            showlegend=False
        )
        return opy.plot(fig, auto_open=False, output_type='div')
    else:
        return None


def manage_missing_language(request, evaluation, **kwargs):
    """
    If the user wants to change the language of the platform while not having the evaluation in the same
    language, reactive the language of the evaluation
    """
    lang_code = get_language_from_request(request)
    if lang_code not in evaluation.assessment.get_the_available_languages():
        valid_lang = "fr"
        # messages.warning(request, _("Your evaluation has not this language"))
        request.session[LANGUAGE_SESSION_KEY] = valid_lang
        activate(valid_lang)


def treat_delete_note(request):
    """
    This function treats the POST methods when the user delete a note on the profile page.
    It checks if the note exist and if the user can delete the note.
    If so the note is deleted and a successful response is returned.
    Else nothing appends and an error response is returned
    """
    user = request.user
    element_id = request.POST.dict().get("note_element_id")
    try:
        # try to get an element that matchs the specified id, that has note and that the user can delete it
        element = (
            EvaluationElement.objects.filter(id=element_id)
            .filter(
                Q(
                    section__evaluation__organisation__membership__user=user,
                    section__evaluation__organisation__membership__role="admin",
                )
                | Q(
                    section__evaluation__organisation__membership__user=user,
                    section__evaluation__organisation__membership__role="editor",
                )
            )
            .exclude(user_notes__isnull=True)
            .get()
        )
        element.user_notes = None
        element.save()
        response = {
            "success": True,
            "message_type": "alert-success",
            "message": _("Your note has been deleted!"),
            "section_id": element.section.id,
            "evaluation_id": element.section.evaluation.id,
        }
        return HttpResponse(json.dumps(response), content_type="application/json")
    except ObjectDoesNotExist as e:
        # if the element is not found returns an error
        logger.error(
            f"[user_note_error] The element id {element_id} from the post of "
            f"the user {request.user.email} is not an element or the user can't access it"
        )
        return error_500_view_handler(request, exception=e)
