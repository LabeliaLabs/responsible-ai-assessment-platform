# TODO split this file in a folder with one python file by class

"""
This file is used to define and update objects which will be displayed in the templates (html files)
The class views are called in the url file.

"""
import json
import markdown
import requests
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404, get_list_or_404, render
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.utils.translation import gettext as _

from .models import (
    Assessment,
    Evaluation,
    Choice,
    Section,
    EvaluationElement,
    ExternalLink,
    get_last_assessment_created,
)
from .forms import (
    EvaluationForm,
    ChoiceForm,
    ResultsForm,
    ElementFeedbackForm,
    element_feedback_list,
    SectionFeedbackForm,
    section_feedback_list,
)
from home.models import Organisation
from django.conf import settings

private_token = settings.PRIVATE_TOKEN
project_id = str(settings.PROJECT_ID)


# As we get the organisation id in the url, we need to be sure that the user is a member of the organisation called
# in the url


def membership_security_check(request, *args, **kwargs):
    """
    This function checks that the user is member of the organisation.
    It gets the user in the request and the organisation in the kwargs.
    If the organisation doesn't exist, it renders a 404.
    If the user is not member, it renders a 403.
    If the user is member of the organisation, the function returns nothing
    This is used in all the CBV where we need to be sure the user is member of the organisation
    """
    user = request.user
    organisation = kwargs.get("organisation", None)
    # If we don't have the organisation in the kwargs
    if organisation is None:
        organisation_id = kwargs.get("orga_id", None)
        organisation = get_object_or_404(Organisation, id=organisation_id)
    is_member = organisation.check_user_is_member(user=user)
    return is_member


def membership_admin_security_check(request, *args, **kwargs):
    """
    This function checks that the user is member as ADMIN of the organisation.
    It gets the user in the request and the organisation in the kwargs.
    If the organisation doesn't exist, it renders a 404.
    If the user is not an admin member, it renders a 403.
    If the user is an admin member of the organisation, the function returns nothing
    This is used in all the CBV where we need to be sure the user is an admin member of the organisation (evaluation
    deletion, accept other users, ...)
    """
    user = request.user
    organisation = kwargs.get("organisation", None)
    # If we don't have the organisation in the kwargs
    if organisation is None:
        organisation_id = kwargs.get("orga_id", None)
        organisation = get_object_or_404(Organisation, id=organisation_id)
    is_member_as_admin = organisation.check_user_is_member_as_admin(user=user)
    return is_member_as_admin


def upgradeView(request, *args, **kwargs):
    # print("UPGRADE VIEW", kwargs, request.POST.dict())
    user = request.user
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist
    # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
    if not membership_security_check(
        request, organisation=organisation, *args, **kwargs
    ):
        messages.warning(request, _("You don't have access to this content."))
        return redirect("home:homepage")

    evaluation_id = kwargs.get("pk")
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    evaluation_version = evaluation.assessment.version
    latest_version = get_last_assessment_created().version
    # print("compare versions", evaluation_version, latest_version)
    if float(evaluation_version) < float(latest_version):
        success = False
        try:
            # todo logs
            new_eval = evaluation.upgrade(user=user)
            success = True
        except ValueError:
            # todo logs
            messages.warning(request, _("We are sorry, the operation failed."))
            url = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        if success:
            previous_url = request.META.get("HTTP_REFERER")
            print("previous URL", previous_url, kwargs)
            # Todo can factorize this and redirect to the section
            if "/section/" in previous_url:
                # url = redirect("assessment:section", organisation.id, new_eval.slug, new_eval.pk)
                messages.success(
                    request,
                    _(
                        "Your evaluation has been upgraded! You have been redirected to it."
                    ),
                )
                url = redirect(
                    "assessment:evaluation", organisation.id, new_eval.slug, new_eval.pk
                )
            elif "/results/" in previous_url:
                url = redirect(
                    "assessment:evaluation", organisation.id, new_eval.slug, new_eval.pk
                )
                messages.success(
                    request,
                    _(
                        "Your evaluation has been upgraded! You have been redirected to it. "
                        "You have to complete the new items before the validation."
                    ),
                )
            elif "/profile/" in previous_url:
                url = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
                messages.success(request, _("Your evaluation has been upgraded!"))
            elif (
                "organisation" in previous_url
                and not str(evaluation_id) in previous_url
            ):
                url = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
                messages.success(request, _("Your evaluation has been upgraded!"))
            # Case it is the evaluation page
            else:
                url = redirect(
                    "assessment:evaluation", organisation.id, new_eval.slug, new_eval.pk
                )
                messages.success(
                    request,
                    _(
                        "Your evaluation has been upgraded! You have been redirected to it."
                    ),
                )

    else:
        url = HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        messages.warning(request, _("There is an issue with the versions."))
    return url


class SummaryView(LoginRequiredMixin, DetailView):
    model = Organisation
    template_name = "assessment/organisation.html"
    form_class = EvaluationForm
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):
        """Overrride the get method to order by created_at desc"""

        # Get the organisation from the url
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(
            Organisation, id=organisation_id
        )  # Get 404 if orga_id doesn't exist
        # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
        if not membership_security_check(
            request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")

        print("KWARGS", kwargs)

        self.object = organisation
        context = self.get_context_data(object=self.object)
        context["organisation"] = organisation
        # Can be empty
        context["evaluation_list"] = Evaluation.objects.filter(
            organisation=organisation
        ).order_by("-created_at")
        context["form"] = EvaluationForm()
        # TODO other way to find the last version, not relying on the creation date
        if get_last_assessment_created():
            context[
                "last_version"
            ] = get_last_assessment_created().version  # get last version
        else:
            context["last_version"] = get_last_assessment_created()
        # print("GEEEET", self.object_list, context)
        context["member_list"] = organisation.get_list_members_not_staff()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        print("CALL THE POST")

        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        if not membership_security_check(
            request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")

        # Check if the user is an admin member of the orga, if not, return to the same page
        if not membership_admin_security_check(
                request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have the right to do this action."))
            return redirect("assessment:orga-summary", organisation.id)

        # When creating an evaluation
        if request.method == "POST":
            user = request.user
            # create a form instance and populate it with data from the request:
            form = EvaluationForm(request.POST)
            # print("FORM POST", request.POST.dict())
            dic_form = request.POST.dict()
            # check whether it's valid:
            if form.is_valid():
                name = dic_form.get("name")
                # Store the last evaluation version before the evaluation creation
                last_version_in_organisation = (
                    organisation.get_last_assessment_version()
                )
                eval = Evaluation.create_evaluation(
                    name=name,
                    assessment=get_last_assessment_created(),
                    organisation=organisation,
                    user=user,
                )
                eval.create_evaluation_body()
                # Check if we need to fetch the evaluation
                print(
                    "last eval, test fetch",
                    last_version_in_organisation,
                    get_last_assessment_created().version,
                )
                if (
                    last_version_in_organisation
                    and last_version_in_organisation
                    < float(get_last_assessment_created().version)
                ):
                    print("fetch eval", eval)
                    origin_assessment = get_object_or_404(
                        Assessment, version=str(last_version_in_organisation)
                    )
                    eval.fetch_the_evaluation(origin_assessment=origin_assessment)

                # redirect to a new URL:
                response = redirect(
                    "assessment:evaluation", organisation.id, eval.slug, eval.pk,
                )
                return response


class EvaluationCreationView(LoginRequiredMixin, CreateView):
    """
    This Class View is used only when the user wants to create his evaluation from his profile
    having no organisation set yet
    """

    model = Evaluation
    form_class = EvaluationForm
    template_name = "assessment/creation-evaluation.html"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(
            request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")
        self.object = None
        context = self.get_context_data()
        context["last_version"] = get_last_assessment_created().version
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            organisation_id = kwargs.get("orga_id")
            organisation = get_object_or_404(Organisation, id=organisation_id)
            # Check if the user is member of the orga, if not, return HttpResponseForbidden
            if not membership_security_check(
                    request, organisation=organisation, *args, **kwargs
            ):
                messages.warning(request, _("You don't have access to this content."))
                return redirect("home:homepage")

            # Check if the user is an admin member of the orga, if not, return to the same page
            if not membership_admin_security_check(
                    request, organisation=organisation, *args, **kwargs
            ):
                messages.warning(request, _("You don't have the right to do this action."))
                return redirect("home:user-profile")

            form = EvaluationForm(request.POST)
            dic_form = request.POST.dict()
            user = request.user
            # check whether it's valid:
            print("POST EVAL", dic_form)
            if form.is_valid():
                name = dic_form.get("name")
                eval = Evaluation.create_evaluation(
                    name=name,
                    assessment=get_last_assessment_created(),
                    organisation=organisation,
                    user=user,
                )
                eval.create_evaluation_body()
                # redirect to a new URL:
                response = redirect(
                    "assessment:evaluation", organisation.id, eval.slug, eval.pk,
                )
                return response
            else:
                return self.form_invalid(form)


class DeleteEvaluation(LoginRequiredMixin, DeleteView):
    model = Evaluation
    success_url = "home:user-profile"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def delete(self, request, *args, **kwargs):

        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(
                request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")

        # Check if the user is an admin member of the orga, if not, return to the same page
        if not membership_admin_security_check(
                request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have the right to do this action."))
            return redirect("assessment:orga-summary", organisation_id)

        self.object = self.get_object()
        print("DELETE", dir(request), request.get_full_path)

        self.object.delete()

        # Manage the redirection, if the user delete the evaluation from his profile, it redirect to his profile
        # If the user does the suppression from the organisation, redirect to the organisation
        previous_url = request.META.get("HTTP_REFERER")
        print("DELETION EVAL, test previous_url", previous_url)
        return HttpResponseRedirect(previous_url)


class EvaluationView(LoginRequiredMixin, DetailView):
    model = Evaluation
    template_name = "assessment/evaluation.html"
    context_object_name = "evaluation"
    pk_url_kwarg = "pk"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(
            request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")

        evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"))
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # I dont know why I cannot do in one line: list.sort() (test in shell not working)
        section_list_ = get_list_or_404(Section, evaluation=evaluation)
        section_list = sorted(
            section_list_, key=lambda x: x.master_section.order_id
        )  # sort the list
        context["section_list"] = section_list
        # print("EVALUATION", context)
        context["organisation"] = organisation
        context["evaluation_form_dic"] = {str(evaluation.id): EvaluationForm(name=evaluation.name)}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            organisation_id = kwargs.get("orga_id")
            organisation = get_object_or_404(Organisation, id=organisation_id)
            if not membership_admin_security_check(
                    request, organisation=organisation, *args, **kwargs
            ):
                messages.warning(request, _("You don't have the right to do this action."))
                return HttpResponseRedirect(self.request.path_info)
            if "name" in request.POST.dict() and request.is_ajax():
                data_update = {"success": False, "message": _("An error occurred")}
                form = EvaluationForm(request.POST)
                if form.is_valid():
                    name = form.cleaned_data.get("name")
                    evaluation_id = int(request.POST.dict().get("evaluation_id"))
                    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
                    evaluation.name = name
                    evaluation.save()
                    data_update["success"] = True
                    data_update["message"] = _("The evaluation's name has been changed")
                return HttpResponse(json.dumps(data_update), content_type="application/json")
            return HttpResponseRedirect(self.request.path_info)


class ResultsView(LoginRequiredMixin, DetailView):
    # Results of the evaluation with the score
    model = Evaluation
    template_name = "assessment/results.html"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):
        # TODO only if evaluation is finished
        # TODO change way the score is calculated (on change)
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(
            request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")
        print("RESULT", dir(request))
        # evaluation_id = kwargs.get("pk")  # TODO if not used, to delete
        evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"))
        # If the evaluation is finished, which should always be the case here, set the score of the evaluation
        if evaluation.is_finished:
            # print("SET SCOREEEE")
            points_not_concerned = evaluation.calculate_sum_points_not_concerned()
            coeff_scoring_system = evaluation.get_coefficient_scoring_system()
            points_obtained = evaluation.calculate_points_obtained(
                points_not_concerned, coeff_scoring_system
            )
            points_to_dilate = evaluation.calculate_points_to_dilate(
                coeff_scoring_system, points_obtained, points_not_concerned
            )
            max_possible_points = evaluation.calculate_max_points()
            dilatation_factor = evaluation.calculate_dilatation_factor(
                coeff_scoring_system, max_possible_points, points_not_concerned
            )
            evaluation.set_score(
                dilatation_factor,
                points_to_dilate,
                points_not_concerned,
                coeff_scoring_system,
                max_possible_points,
            )
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context["dic_form_results"] = set_form_for_results(evaluation=evaluation)
        context["section_list"] = list(
            evaluation.section_set.all().order_by("master_section__order_id")
        )
        context["evaluation_element_list"] = evaluation.get_list_all_elements()
        context["organisation"] = organisation
        return self.render_to_response(context)


class SectionView(LoginRequiredMixin, ListView):
    """
    ListView for the sections of an evaluation
    The form is created with ChoiceForm for each evaluation element
    The pagination is one section by page
    """

    model = Section
    template_name = "assessment/section.html"
    paginate_by = 1
    # form_class = ChoiceForm
    success_url = "assessment:results"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def post(self, request, *args, **kwargs):
        """

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
            if not membership_security_check(
                    request, organisation=organisation, *args, **kwargs
            ):
                messages.warning(request, _("You don't have access to this content."))
                return redirect("home:homepage")

            # If the ajax, if when the user likes/unlikes a resource
            if "resource_id" in request.POST.dict():
                return treat_resources(request)

            # If in the ajax post is for element feedback
            elif "element_feedback_type" in request.POST.dict():
                return treat_feedback(request, "element")

            # If in the ajax post is for element feedback
            elif "section_feedback_type" in request.POST.dict():
                return treat_feedback(request, "section")

            # Else, it s when the user validates an answer
            else:
                # Get ids of the objects Section and Evaluation from the url
                # evaluation_id = kwargs.get("pk") # todo remove if not used
                evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"))

                # Check if the user is an admin member of the orga, if not, he is redirected to the evaluation summary
                if not membership_admin_security_check(
                        request, organisation=organisation, *args, **kwargs
                ):
                    # This is a security with an error message telling the user he cannot do the action (validate an
                    # answer). Normally, the button is disabled for non-admin user of the organisation
                    data_update = {
                        "conditional_elements_list": [],
                        "success": False,
                        "conditions_respected": True,
                        "element_status_changed": False,
                        "no_more_condition_inter": False,
                        "message": _("You don't have the right to do this action.")
                    }
                    return HttpResponse(json.dumps(data_update), content_type="application/json")

                section_query = get_list_or_404(
                    Section, evaluation=evaluation
                )  # List or 404
                evaluation_element_id = request.POST.get("element_id")
                evaluation_element = get_object_or_404(
                    EvaluationElement, id=int(evaluation_element_id)
                )

                # Process the form
                form = ChoiceForm(request.POST, evaluation_element=evaluation_element)

                # create context used in the process of a valid form
                self.object_list = section_query
                context = self.get_context_data()
                context["evaluation"] = evaluation

                # create a dic from the POST values (evaluation element form values)
                dic_choices = request.POST.dict()

                context["organisation"] = organisation
                if form.is_valid():
                    return self.treat_valid_form(
                        context, evaluation_element, request, dic_choices, form
                    )
                else:
                    return self.handle_invalid_form(context, kwargs)

    def get(self, request, *args, **kwargs):
        """
        Override the method to add data in the context (form, pagination)
        Parameters (evaluation id, section id) are caught from the kwargs

        :param request: GET request
        :param args:
        :param kwargs: data stored in the url
        :return:
        """

        # TODO possibility of change only if user admin

        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(
            request, organisation=organisation, *args, **kwargs
        ):
            messages.warning(request, _("You don't have access to this content."))
            return redirect("home:homepage")

        # Get ids and objects form the url
        evaluation_id = kwargs.get("pk")
        evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"))
        section_query = self.get_queryset(evaluation_id=evaluation_id)
        self.object_list = section_query
        # print("GET", evaluation_id, kwargs, list(section_query))

        # Create the context and add the list of the sections
        context = self.get_context_data()
        context["section_list"] = list(
            section_query
        )  # used in section.html to cover all the section

        # Create the form for each evaluation element and add it to context, used in evaluation element cards
        context["dic_form"] = set_form_for_sections(section_query)

        # Add the evaluation to context, used in templates to go back to evaluation page
        context["evaluation"] = evaluation

        # Order the list of evaluation elements by order_id
        section = get_object_or_404(Section, id=kwargs.get("id"))
        context["element_list"] = list(
            section.evaluationelement_set.all().order_by(
                "master_evaluation_element__order_id"
            )
        )

        # Manage dynamic conditions between evaluation elements in a dictionary depends_on_dic
        # This dictionary is used in the case an element is not available to inform the user that this is due
        # to the answer in this other evaluation element
        context["depends_on_dic"] = {}
        for element in context["element_list"]:
            context["depends_on_dic"][element] = element.get_element_depending_on()

        # Feedback for the element and section
        context["element_feedback_form"] = ElementFeedbackForm()
        context["section_feedback_form"] = SectionFeedbackForm()

        # Manage pagination and next/previous section
        num_page = kwargs.get("page")
        num_page = int(num_page)
        # If there is a previous section
        if num_page > 1:
            context["previous_section"] = list(section_query)[num_page - 2]
        else:
            context["previous_section"] = None
        # If there is a next section
        if num_page < len(list(section_query)):
            context["next_section"] = list(section_query)[num_page]
        else:
            context["next_section"] = None

        context["organisation"] = organisation
        # List of the resources liked by the user
        context["resources_liked"] = request.user.userresources.resources.all()
        return self.render_to_response(context)

    def get_queryset(self, *args, **kwargs):
        """Override the class method to have only the sections belonging to the evaluation"""
        queryset = super().get_queryset()
        evaluation_id = kwargs.pop("evaluation_id")
        if type(evaluation_id) == int:
            queryset = self.model.objects.filter(evaluation__id=evaluation_id).order_by(
                "master_section__order_id"
            )  # order according to master section
        return queryset

    def treat_valid_form(self, context, evaluation_element, request, dic_choices, form):
        """
        This function is used to treat valid form after a POST method by the user in section.html (when a user validate
        a choice for an evaluation element). As it s an ajax request, we do not refresh the page, just save the
        modifications (choice selected, notes), update the section progress bar and inform that it s a success
        in order to display a success alert.

        :param context: used to
        :param evaluation_element:
        :param request:
        :param dic_choices:
        :return:
        """
        # Data_update is the dictionary which will store the info sent back to the ajax function
        # For this evaluation element, if one or several choices ticked (or unticked) set conditions on
        # other evaluation element, we need to store the list of them, actually in 'conditional_element_list'
        data_update = {
            "conditional_elements_list": [],
            "success": False,
            "conditions_respected": True,
            "element_status_changed": False,
            "no_more_condition_inter": False,
        }

        # We need to update the evaluation element icon status only if it has changed
        initial_element_status = evaluation_element.status

        # Check if the element currently disable other elements
        if (
            evaluation_element.condition_on_other_elements()
            and evaluation_element.get_choice_setting_conditions_on_other_elements().is_ticked
        ):
            # So at this point we know that the element disable another element and the choice doing this is ticked
            # So we need to check if this choice is still ticked or not
            if evaluation_element.get_choice_setting_conditions_on_other_elements() not in request.POST.getlist(
                str(evaluation_element.id)
            ):
                data_update["no_more_condition_inter"] = True

        # If there is at least one choice ticked
        if str(evaluation_element.id) in dic_choices.keys():

            # Case the notes have changed
            if dic_choices["notes"] != form.fields["notes"].initial:
                # Temporary attribute the notes to the element, will be saved later if the the choices are valid
                # Need to see if independent saving or not
                evaluation_element.user_notes = form.cleaned_data.get("notes")

            # List_choices_ticked contains all the choices selected for this evaluation element, useful for checkbox
            # where several choices can be selected
            list_choices_ticked = request.POST.getlist(str(evaluation_element.id))

            # List of all the choices of the evaluation element in order to compare with those ticked/unticked
            list_choices_element = list(
                Choice.objects.filter(evaluation_element=evaluation_element)
            )

            # Test if the are conditions inside the evaluation element and if there are verified
            if evaluation_element.are_conditions_between_choices_satisfied(
                list_choices_ticked
            ):

                # For all the choices of the evaluation element
                for choice in list_choices_element:

                    # If this choice is ticked
                    if str(choice) in list_choices_ticked:
                        # It is saved with the value 'is_ticked' as True
                        choice.is_ticked = True
                        choice.save()

                        # And if this choice turns other evaluation elements not applicable The id of the evaluation
                        # elements which won't be available due to this choice are added to list

                        if choice.get_list_element_depending_on():
                            for element_ in choice.get_list_element_depending_on():
                                data_update["conditional_elements_list"].append(
                                    str(element_.id)
                                )
                                element_.reset_choices()
                                element_.status = False
                                element_.save()

                    # If the choice is not ticked, we ensure to have his attribute 'is_ticked' to False and save it
                    else:
                        choice.is_ticked = False
                        choice.save()

                # The choices have been successfully updated
                data_update["success"] = True
                # todo : bug with ugettext (no translation), and I tried gettext_lazy with LazyEncoder class but not
                #  working either .. When I check the string in the view, it is still in english.
                #  I checked the translation in django.po and no pb seen
                # data_update["message"] = _("Your answer has been saved!")
                data_update["message"] = "Votre réponse a bien été sauvegardée !"

            # the conditions between choices inside the evaluation element are not respected, we return an alert
            # message
            else:
                data_update["success"] = False
                data_update["conditions_respected"] = False
                # todo : solve bug
                # data_update["message"] = (
                #    _("You can not combine these answers. The answer hasn't been saved. ")
                # )
                data_update["message"] = (
                    "Vous ne pouvez pas combiner ces deux choix, "
                    "votre réponse n'a pas été sauvegardée."
                )

        # If there is no choice ticked (unselect all for checkbox or reset choices)
        # So the evaluation element status is set to False (not answered) and all choices.is_ticked are set to False
        else:
            print("ELSE NO TICKED")
            # If the element we rest the choice sets conditions on other elements
            if evaluation_element.condition_on_other_elements:
                # If we reset the choices of the element and among the choices, one set condition on other elements,
                # We add this information in data_update and in the jquery, we will remove the warning messages
                # And set the conditioned elements not to disabled
                if (
                    evaluation_element.get_choice_setting_conditions_on_other_elements()
                    in evaluation_element.get_list_choices_ticked()
                ):
                    choice_setting_conditions = (
                        evaluation_element.get_choice_setting_conditions_on_other_elements()
                    )
                    for (
                        element_
                    ) in choice_setting_conditions.get_list_element_depending_on():
                        data_update["conditional_elements_list"].append(
                            str(element_.id)
                        )

            evaluation_element.reset_choices()
            # todo : solve bug
            # data_update["message_reset"] = _("Your answers have been reset!")
            data_update["message_reset"] = "Votre réponse a bien été réinitialisée."
            # If the notes have changed
            if (
                "notes" in dic_choices
                and dic_choices["notes"] != form.fields["notes"].initial
            ):
                # Get and save the notes
                evaluation_element.user_notes = form.cleaned_data.get("notes")
                evaluation_element.save()

            data_update["success"] = True
            # data_update["message"] = _("Your answer has been updated.")
            data_update["message"] = "Votre réponse a bien été mise à jour."

        # Update the section status and the evaluation status
        evaluation_element.set_status()
        evaluation_element.set_points()
        # get the section
        section = evaluation_element.section
        section.set_progression()
        section.set_points()
        # If all the other evaluation element are answered and this one is the last
        # The evaluation.is_finished attribute is set to True, else False
        evaluation = context["evaluation"]
        evaluation.set_finished()

        # The progression and status are added to the data_update dictionary
        data_update["section_progression"] = section.user_progression
        data_update["evaluation_element_treated"] = evaluation_element.status
        data_update["evaluation_finished"] = evaluation.is_finished
        print("evaluation finished ?", evaluation.is_finished)
        if evaluation_element.status != initial_element_status:
            data_update["element_status_changed"] = True

        print("DAT UPDATE", data_update)
        return HttpResponse(json.dumps(data_update), content_type="application/json")

    def handle_invalid_form(self, request, *args, **kwargs):
        """
        This function treat invalid form. There will be an error message displayed

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        data_update = {
            "conditional_elements_list": [],
            "success": False,
            "conditions_respected": True,
            "message": _("An issue occured, please try again."),
        }

        return HttpResponse(json.dumps(data_update), content_type="application/json")


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
                evaluation_element=evaluation_element
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
                evaluation_element=evaluation_element
            )
    return dic_form


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
    data_update = {
        "success": False,
        "message": _(
            "We are sorry but the message hasn't been sent. "
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
        error_500_view_handler(request, exception=None)

    if form.is_valid():
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
                error_500_view_handler(request, exception=e)
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
                error_500_view_handler(request, exception=e)
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
                if (
                    response.status_code == 200 or response.status_code == 201
                ):  # if 200 or 201 for created
                    data_update["success"] = True
                    data_update["message"] = _(
                        "Thank you for your feedback, it helps us a lot!"
                        " We will take it into consideration as soon as possible"
                    )
            except requests.exceptions.RequestException as e:
                # todo logs
                print(f"error in requests {e}")
                pass
        else:
            data_update["message"] = _(
                "Please, do not spam the feature. If your are not, contact the support service!"
            )

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
        #    print("end loop", "i", i, "count", count)
        # print("compare count and max", count, max_feedback )
    return count > max_feedback


# Error management #

# TODO split in another file

VIEW_ERRORS = {
    404: {
        "title": _("404 - Page not found"),
        "content": _("Sorry, the page has not been found or does not exist !"),
    },
    500: {"title": _("Internal error"), "content": _("An internal error occured"), },
    403: {
        "title": _("Permission denied"),
        "content": _("Sorry, you can not access this content"),
    },
    400: {"title": _("Bad request"), "content": _("There is an error in the request"), },
}


def error_view_handler(request, exception, status):
    return render(
        request,
        template_name="errors.html",
        status=status,
        context={
            "error": exception,
            "status": status,
            "title": VIEW_ERRORS[status]["title"],
            "content": VIEW_ERRORS[status]["content"],
        },
    )


def error_404_view_handler(request, exception=None):
    print("error 404")
    return error_view_handler(request, exception, 404)


def error_500_view_handler(request, exception=None):
    print("error 500")
    return error_view_handler(request, exception, 500)


def error_403_view_handler(request, exception=None):
    messages.warning(request, _("You don't have access to this content."))
    print(f"ERREUR 403, {exception}")
    return HttpResponseRedirect("/home/")
    # return redirect("home:homepage")
    # return error_view_handler(request, exception, 403)


def error_400_view_handler(request, exception=None):
    return error_view_handler(request, exception, 400)
