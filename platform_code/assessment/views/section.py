import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.views.generic import ListView
from django.utils.translation import gettext as _
from django.shortcuts import redirect, get_object_or_404

from assessment.forms import SectionNotesForm, ChoiceForm, ElementFeedbackForm, SectionFeedbackForm
from assessment.models import Section, Evaluation, EvaluationElement, EvaluationScore
from assessment.utils import get_client_ip
from assessment.views.utils.security_checks import can_edit_security_check, membership_security_check
from assessment.views.utils.treat_feedback_and_resources import treat_resources, treat_feedback
from assessment.views.utils.utils import set_form_for_sections
from home.models import Organisation

logger = logging.getLogger('monitoring')


class SectionView(LoginRequiredMixin, ListView):
    """
    ListView for the sections of an evaluation
    The form is created with ChoiceForm for each evaluation element
    The pagination is one section by page
    """

    model = Section
    template_name = "assessment/section.html"
    paginate_by = 1
    success_url = "assessment:results"
    login_url = "home:login"
    redirect_field_name = "home:homepage"
    context = {}
    data_update = {"success": False, "message": _("An error occurred."), "message_type": "alert-danger"}

    def get(self, request, *args, **kwargs):
        """
        Override the method to add data in the context (form, pagination)
        Parameters (evaluation id, section id) are caught from the kwargs

        :param request: GET request
        :param args:
        :param kwargs: data stored in the url
        :return:
        """

        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(request, organisation=organisation):
            return redirect('home:homepage')

        # Get ids and objects form the url
        evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"), organisation=organisation)
        section_query = self.get_queryset(evaluation=evaluation)
        self.object_list = section_query

        # Create the context and add the list of the sections
        self.context = self.get_context_data()
        self.context["section_list"] = list(section_query)  # used in section.html to cover all the section

        # Create the form for each evaluation element and add it to context, used in evaluation element cards
        self.context["dic_form"] = set_form_for_sections(section_query)

        # Add the evaluation to context, used in templates to go back to evaluation page
        self.context["evaluation"] = evaluation

        # Order the list of evaluation elements by order_id
        section = get_object_or_404(Section, id=kwargs.get("id"), evaluation=evaluation)
        self.context["element_list"] = list(
            section.evaluationelement_set.all().order_by(
                "master_evaluation_element__order_id"
            )
        )

        # Get the form for section notes
        self.context["section_notes_form"] = SectionNotesForm(
            section=section,
            user_can_edit=organisation.check_user_is_member_and_can_edit_evaluations(user=request.user)
        )

        # Manage dynamic conditions between evaluation elements in a dictionary depends_on_dic
        # This dictionary is used in the case an element is not available to inform the user that this is due
        # to the answer in this other evaluation element
        self.context["depends_on_dic"] = {}
        for element in self.context["element_list"]:
            self.context["depends_on_dic"][element] = element.get_element_depending_on()

        # Feedback for the element and section
        self.context["element_feedback_form"] = ElementFeedbackForm(auto_id=False)
        self.context["section_feedback_form"] = SectionFeedbackForm()

        # Manage pagination and next/previous section
        self.manage_pagination(section_query, kwargs.get("page"))

        self.context["organisation"] = organisation
        # List of the resources liked by the user
        self.context["resources_liked"] = request.user.userresources.resources.all()
        return self.render_to_response(self.context)

    def get_queryset(self, *args, **kwargs):
        """
        Override the class method to have only the sections belonging to the evaluation
        """
        queryset = super().get_queryset()
        evaluation = kwargs.pop("evaluation")
        if isinstance(evaluation, Evaluation):
            queryset = self.model.objects.filter(evaluation=evaluation).order_by(
                "master_section__order_id"
            )  # order according to master section
        return queryset

    def manage_pagination(self, section_query, num_page):
        num_page = int(num_page)
        # If there is a previous section
        if num_page > 1:
            self.context["previous_section"] = list(section_query)[num_page - 2]
        else:
            self.context["previous_section"] = None
        # If there is a next section
        if num_page < len(list(section_query)):
            self.context["next_section"] = list(section_query)[num_page]
        else:
            self.context["next_section"] = None

    def post(self, request, *args, **kwargs):
        """
        This method treat the POST http requests in the section page which can consist in:
            - giving a feedback on a evaluation element (externalized)
            - giving a feedback on a section (externalized)
            - liking/unliking resources (externalized)
            - updating the section notes
            - updating an evaluation element answer (choices or notes)
            - resetting the evaluation element responses

        The evaluation elements may have conditions set on them (conditions inter) or may have conditions
        on their own choices (condition intra) that we need to check before validating and saving the answer,
        independently of saving evaluation element notes.

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # If the user submit the form for an evaluation element

        if request.method == "POST":
            # We allow the simple user to like resources, to give feedback !
            # The user which is not member of the orga is redirected to the homepage
            organisation_id = kwargs.get("orga_id")
            organisation = get_object_or_404(Organisation, id=organisation_id)
            if not membership_security_check(request, organisation=organisation):
                return redirect("home:homepage")

            # Evaluation must have this organisation in its fields organisation
            evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"), organisation=organisation)

            section = get_object_or_404(Section, id=kwargs.get("id"), evaluation=evaluation)

            if request.is_ajax():
                # If the ajax, if when the user likes/unlikes a resource
                if "resource_id" in request.POST.dict():
                    # Function externalized because used also in ResourceView class
                    return treat_resources(request)

                # If in the ajax post is for element feedback
                elif "element_feedback_type" in request.POST.dict():
                    # Function externalized because used also in ProfileView class
                    return treat_feedback(request, "element", evaluation=evaluation)

                # If in the ajax post is for element feedback
                elif "section_feedback_type" in request.POST.dict():
                    # Function externalized because used also in ProfileView class
                    return treat_feedback(request, "section", evaluation=evaluation)

                # The action requires the edit/admin role of the user inside the organisation
                # The treatment of the post method is done inside the class (not externalized)
                else:
                    if not can_edit_security_check(request, organisation=organisation):
                        self.data_update["message"] = _("You don't have the right to do this action.")
                    # User has the right to do an action
                    else:
                        # If the user writes notes for the section
                        if "notes_section_id" in request.POST:
                            self.treat_section_notes(request, section)

                        # If the user resets the evaluation elements choices, can save notes if modified
                        elif "reset_element_id" in request.POST:
                            evaluation_element = get_evaluation_element_with_logs(request=request,
                                                                                  section=section,
                                                                                  element_id_name="reset_element_id")
                            # If the evaluation elements exist for this section with the id provided by ajax post
                            # Else, do not treat the post, response is "an error occurred"
                            if evaluation_element:
                                if evaluation_element.is_applicable():
                                    self.treat_reset_element(request, evaluation, evaluation_element)
                                    self.treat_element_notes(request, evaluation_element)
                                else:
                                    self.manage_evaluation_element_not_applicable(request, evaluation_element)

                        # Element choices validation and/or notes
                        else:
                            evaluation_element = get_evaluation_element_with_logs(request=request,
                                                                                  section=section,
                                                                                  element_id_name="element_id")
                            # If the evaluation elements exist for this section with the id provided by ajax post
                            # Else, do not treat the post, response is "an error occurred"
                            if evaluation_element:
                                if evaluation_element.is_applicable():
                                    self.treat_element_notes(request, evaluation_element)
                                    self.treat_element_validation(request, evaluation, evaluation_element)
                                else:
                                    self.manage_evaluation_element_not_applicable(request, evaluation_element)

                    return HttpResponse(json.dumps(self.data_update), content_type="application/json")

    def treat_section_notes(self, request, section):
        """
        This function treat the case the user changes the section notes.
        If the form is valid, update the message to say success!
        """
        # As the user has edit or admin role, the value "user_can_edit" is set to True to not disable the form
        form = SectionNotesForm(request.POST, user_can_edit=True)
        # Treat the case if the form is valid
        # Else the form is invalid, the default message is let and displayed to the user "an issue occurred"
        if form.is_valid():
            notes = form.cleaned_data.get("user_notes")
            # The section is get above, according to the url
            if section:
                # To be sure the notes are for the section the user is dealing with
                section.user_notes = notes
                section.save()
                self.data_update["success"] = True
                self.data_update["message"] = _("Your notes have been saved!")
                self.data_update["message_type"] = "alert-success"
        else:
            logger.warning(f"[invalid_form] The user {request.user.email} tries to save section notes (section id "
                           f"{section.id} but the form is invalid")

    def treat_element_notes(self, request, evaluation_element):
        """
        Treat the saving of the element notes.
        If the form is valid and the notes has changed, new key in data_update, which is different than "message" as
        can both change notes and answers.
        """
        self.data_update["message_notes"] = None  # We suppose there is no notes, initialization
        form = ChoiceForm(request.POST, evaluation_element=evaluation_element, prefix=evaluation_element.id)
        if form.is_valid():
            element_notes = form.cleaned_data.get("notes")
            # Case the notes have changed, else no message
            if element_notes and element_notes != form.fields["notes"].initial:
                evaluation_element.user_notes = element_notes
                evaluation_element.save()
                # Update only the note message and not the "message" key nor "success"
                self.data_update["message_notes"] = _("Your notes have been saved!")
                self.data_update["message_notes_type"] = "alert-success"

        else:
            logger.warning(f"[invalid_form] The user {request.user.email} tries to save notes for an evaluation element"
                           f"(id {evaluation_element.id} but the form is invalid")
            self.data_update["message_notes"] = _("Your notes have not been saved, an error occurred.")
            self.data_update["message_notes_type"] = "alert-danger"

    def treat_reset_element(self, request, evaluation, evaluation_element):
        """
        Treat the action "reset element" which:
            - checks if the evaluation element currently sets condition on other elements (data_update new key)
            - resets the choices of the evaluation elements and save it
            - checks if there is a change in the element status (data_update new key)
        """
        initial_element_status = evaluation_element.status
        self.manage_no_more_conditions_inter(request, evaluation_element, reset=True)
        evaluation_element.reset_choices()
        self.manage_element_status_change(initial_element_status, evaluation_element)
        self.data_update["message"] = _("Your answers have been reset!")
        self.data_update["message_type"] = "alert-success"
        self.data_update["success"] = True
        self.manage_evaluation_progression_and_points(request, evaluation, evaluation_element)

    def treat_element_validation(self, request, evaluation, evaluation_element):
        """
        This method treats the different actions to validate an answer of an evaluation element:
            - manage the condition inter evaluation elements in the case they existed before but
            not after the validation
            - validate and save the choices (check condition intra, form, choices list)
            - update the element status
            - update the progression and the points of the element, section, evaluation and set evaluation score to
            "need to be calculated again"
        """
        initial_element_status = evaluation_element.status
        self.manage_no_more_conditions_inter(request, evaluation_element, reset=False)
        self.manage_choice_validation(request, evaluation_element)
        self.manage_element_status_change(initial_element_status, evaluation_element)
        self.manage_evaluation_progression_and_points(request, evaluation, evaluation_element)

    def manage_no_more_conditions_inter(self, request, evaluation_element, reset=False):
        """
        This method is used to manage the case an evaluation element sets conditions on other evaluation elements
        because its choice is ticked but if this choice is no longer ticked (reset or not ticked), we need to
        make all the conditioned evaluation elements available to the user (done in ajax function).
        Here we create a new key "no_more_condition_inter" in data_update dict, False by default.
        """
        # False by default as we suppose there is no condition inter
        self.data_update["no_more_condition_inter"] = False
        # If the evaluation element potentially sets conditions on other element
        if evaluation_element.has_condition_on_other_elements() and \
           evaluation_element.get_choice_setting_conditions_on_other_elements().is_ticked:
            # So at this point we know that the element disable another element and the choice doing this is ticked
            # So we need to check if this choice is still ticked or not
            # if reset, necessarily not ticked
            if reset or evaluation_element.get_choice_setting_conditions_on_other_elements() not in \
                    request.POST.getlist(str(evaluation_element.id)):
                self.data_update["no_more_condition_inter"] = True

    def manage_element_status_change(self, initial_element_status, evaluation_element):
        """
        This function manages the element status change before/after the user action.
        A new key "element_status_changed" is created in data_update dict.
        This is used in the ajax function to call a js function to update the evaluation element status (green circle).
        """
        evaluation_element.set_status()
        if evaluation_element.status != initial_element_status:
            self.data_update["element_status_changed"] = True
        else:
            self.data_update["element_status_changed"] = False

    def manage_choice_validation(self, request, evaluation_element):
        """
        Manage the validation of the choices when the user click on the validation button.
        Two cases:
            - at least one choice ticked (if several, need to check conditions intra) and need to manage condition inter
            - no choice ticked (unticked in checkbox or validation of the notes only) so same process than reset
        """

        self.data_update["conditional_elements_list"] = []
        self.data_update["conditions_respected"] = True
        # This list contains the choices ticked in the form.
        # We need to check that they are really choices of the element.
        # As there is a prefix in the form, the key is like "4-4" for the element_id=4
        list_choices_ticked = request.POST.getlist(
            str(evaluation_element.id) + "-" + str(evaluation_element.id)
        )
        # At least one choice ticked
        if list_choices_ticked:
            # If the evaluation element is a radio item (one choice possible) but several in the ajax POST (user hacked)
            if evaluation_element.master_evaluation_element.question_type == "radio" and len(list_choices_ticked) > 1:
                logger.warning(f"[validation_error][html_forced] The user {request.user.email} tried to validate "
                               f"the answer for the evaluation element (id {evaluation_element.id} but it is a radio"
                               f"and they are {len(list_choices_ticked)} choices")
            else:
                # if the list_choices_ticked contains choices of the evaluation elements
                if evaluation_element.are_choices_valid(list_choices_ticked):
                    # If the condition intra is respected
                    if evaluation_element.are_conditions_between_choices_satisfied(list_choices_ticked):
                        # For all the choices of the evaluation element
                        self.manage_ticking_choices_and_new_condition_inter(evaluation_element, list_choices_ticked)
                        self.data_update["message"] = _("Your answer has been saved!")
                        self.data_update["message_type"] = "alert-success"
                        self.data_update["success"] = True
                    else:
                        self.data_update["conditions_respected"] = False
                        self.data_update["message_type"] = "alert-warning"
                        self.data_update["message"] = (
                            _("You can not combine these answers, please select an appropriate combination of choices.")
                        )

                else:
                    logger.warning(f"[choice_validation_error] The user {request.user.email} wanted to validate the "
                                   f"response to the evaluation element (id {evaluation_element.id}) but it failed"
                                   f"because the choices are not valid {list_choices_ticked}.")
        # If no choice ticked while "validation" it means blank validation/note saving or unticking checkbox
        # (radio cannot be fully unticked)
        else:
            evaluation_element.reset_choices()
            self.data_update["success"] = True
            self.data_update["message"] = _("No answer is selected.")
            self.data_update["message_type"] = "alert-warning"

    def manage_ticking_choices_and_new_condition_inter(self, evaluation_element, list_choices_ticked):
        """
        This method manages the choices of the evaluation element, ticking the choices in list_choices_ticked and
        unticking the others.

        If on choice ticked sets conditions inter, the ids of the elements unavailable are added to the list
        "conditional_elements_list" in data_update.
        """

        for choice in evaluation_element.choice_set.all():
            # If this choice is ticked
            # Search the choice numbering in the list of string of ticked choices (containing choice numbering)
            if any(choice.master_choice.get_numbering() in choice_str for choice_str in list_choices_ticked):
                choice.set_choice_ticked()
                # And if this choice turns other evaluation elements not applicable, the ids of the evaluation
                # elements which won't be available due to this choice are added to list
                if choice.get_list_element_depending_on():
                    for element_ in choice.get_list_element_depending_on():
                        self.data_update["conditional_elements_list"].append(str(element_.id))
                        element_.reset_choices()
            # if the choice is not ticked, set not ticked
            else:
                choice.set_choice_unticked()

    def manage_evaluation_progression_and_points(self, request, evaluation, evaluation_element):
        """
        This method manages the evaluation and section progression & points evolution resulting changes in the
        element choices (reset or validation).
        The evaluation score "need_to_calculate" variable is set to True as we assume the answer is not the same than
        before so the evaluation points have changed.
        If the evaluation is finished for the 1st time, we create a log.

        """
        evaluation_element.set_points()
        # get the section
        section = evaluation_element.section
        section.set_progression()
        section.set_points()
        # If all the other evaluation element are answered and this one is the last
        # The evaluation.is_finished attribute is set to True, else False
        evaluation_already_finished = evaluation.is_finished
        evaluation.set_finished()

        # Set that the score will have to be calculated again as we suppose the evaluation has changed
        evaluation_score = get_object_or_404(EvaluationScore, evaluation=evaluation)
        if not evaluation_score.need_to_calculate:
            evaluation_score.need_to_calculate = True
            evaluation_score.save()

        # The progression and status are added to the data_update dictionary
        self.data_update["section_progression"] = section.user_progression
        self.data_update["evaluation_element_treated"] = evaluation_element.status
        self.data_update["evaluation_finished"] = evaluation.is_finished

        # First time the evaluation is finished
        if not evaluation_already_finished and evaluation.is_finished:
            logger.info(f"[evaluation_finished] The user {request.user.email} has finished his evaluation "
                        f"(id: {evaluation.id}) of the organisation {evaluation.organisation}")

    def manage_evaluation_element_not_applicable(self, request, evaluation_element):
        logger.warning(f"[html_forced] The user {request.user.email} wants to do an action on the evaluation element"
                       f"(id {evaluation_element.id}) while it is not applicable - he should not be able to do this"
                       f"action")
        self.data_update["message"] = _("You cannot do this action.")


def get_evaluation_element_with_logs(request, section, element_id_name):
    """
    This function is used to get an evaluation element object based on an id and a section it belongs to.
    It returns the object if it exists, else None and create a log.
    """
    evaluation_element_id = request.POST.get(element_id_name)
    try:
        evaluation_element = EvaluationElement.objects.get(id=int(evaluation_element_id), section=section)

    # The query failed because the evaluation element id does not belong to the section (user edited html)
    except (MultipleObjectsReturned, ObjectDoesNotExist, ValueError) as e:
        logger.warning(f"[html_forced] The user {request.user.email}, with IP address "
                       f"{get_client_ip(request)} modified the js function to do "
                       f"a POST request {request.POST} on an evaluation element which does not belong to"
                       f"the current evaluation (id {section.evaluation.id}), error {e}")
        evaluation_element = None
    return evaluation_element
