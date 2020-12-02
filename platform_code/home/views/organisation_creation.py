import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.views import FormView
from django.shortcuts import redirect

from assessment.models import get_last_assessment_created
from home.forms import OrganisationCreationForm
from home.models import Organisation
from .utils import organisation_required_message, organisation_creation


logger = logging.getLogger('monitoring')


class OrganisationCreationView(LoginRequiredMixin, FormView):
    """
    When the user wants to create an evaluation where as he hasn't an organisation, we need to create the organisation
    """

    template_name = "home/profile-organisation-creation.html"
    model = Organisation
    login_url = "home:login"
    redirect_field_name = "home:homepage"
    form_class = OrganisationCreationForm
    success_url = "assessment:creation-evaluation"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        # If there already is a message, this means the user activated his account before so no need to display warning
        # message
        if list(messages.get_messages(request)):
            context["skip_button"] = True
        else:
            # Add the message user need to create his organisation
            organisation_required_message(context)
            context["skip_button"] = False
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """If the form is valid, redirect to the supplied URL."""
        form = OrganisationCreationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            organisation = organisation_creation(request, form)
            # redirect to a new URL, evaluation creation if there is an assessment in the DB, else profile:
            if get_last_assessment_created():
                response = redirect("assessment:creation-evaluation", organisation.id)
            else:
                response = redirect("home:user-profile")
            return response
        else:
            return self.form_invalid(form)
