import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, get_list_or_404
from django.views.generic import DetailView, DeleteView, CreateView

from assessment.forms import EvaluationForm
from assessment.models import Evaluation, Section, get_last_assessment_created
from assessment.views.utils.security_checks import membership_security_check, can_edit_security_check
from home.models import Organisation
from .utils.edit_evaluation_name import treat_evaluation_name_edition
from .utils.utils import treat_evaluation_creation_valid_form

logger = logging.getLogger('monitoring')


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
        if not membership_security_check(request, organisation=organisation):
            return redirect('home:homepage')

        evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"), organisation=organisation)
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # I dont know why I cannot do in one line: list.sort() (test in shell not working)
        section_list_ = get_list_or_404(Section, evaluation=evaluation)
        section_list = sorted(
            section_list_, key=lambda x: x.master_section.order_id
        )  # sort the list
        context["section_list"] = section_list
        context["organisation"] = organisation
        context["evaluation_form_dic"] = {str(evaluation.id): EvaluationForm(name=evaluation.name)}
        return self.render_to_response(context)

    def post(self, request, **kwargs):
        if request.method == 'POST':
            organisation_id = kwargs.get("orga_id")
            organisation = get_object_or_404(Organisation, id=organisation_id)
            if not can_edit_security_check(request, organisation=organisation):
                messages.warning(request, _("You don't have the right to do this action."))
                return HttpResponseRedirect(self.request.path_info)
            # Edit the name of the evaluation
            if "name" in request.POST.dict() and request.is_ajax():
                return treat_evaluation_name_edition(request)

            return HttpResponseRedirect(self.request.path_info)


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
        if not membership_security_check(request, organisation=organisation):
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
            if not membership_security_check(request, organisation=organisation):
                return redirect("home:homepage")

            # Check if the user is an admin/edit member of the orga, if not, return to the same page
            if not can_edit_security_check(request, organisation=organisation):
                messages.warning(request, _("You don't have the right to do this action."))
                return redirect("home:user-profile")

            form = EvaluationForm(request.POST)
            user = request.user
            # check whether it's valid:
            if form.is_valid():
                # Create the evaluation and return the redirection to it
                return treat_evaluation_creation_valid_form(form, organisation, user)
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
        if not membership_security_check(request, organisation=organisation):
            return redirect("home:homepage")

        # Check if the user is an admin member of the orga, if not, return to the same page
        # TODO check if we want to limit the right to delete evaluation (edit role can only delete their own eval ?)
        if not can_edit_security_check(request, organisation=organisation):
            messages.warning(request, _("You don't have the right to do this action."))
            return redirect("assessment:orga-summary", organisation_id)

        # Add more security by checking the organisation than the method get_object() which just takes the 'pk'
        self.object = get_object_or_404(Evaluation, id=kwargs.get("pk"), organisation=organisation)

        logger.info(f"[evaluation_deletion] The user {request.user.email} deleted an evaluation {self.object.name}")
        messages.success(request, _("The evaluation %(evaluation)s has been deleted.") % {"evaluation": self.object})
        self.object.delete()

        # Manage the redirection, if the user delete the evaluation from his profile, it redirect to his profile
        # If the user does the suppression from the organisation, redirect to the organisation
        previous_url = request.META.get("HTTP_REFERER")
        return HttpResponseRedirect(previous_url)
