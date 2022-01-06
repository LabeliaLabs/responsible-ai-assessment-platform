import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import MultipleObjectsReturned
from django.views import generic

from home.models import User
from assessment.views.utils.error_handler import error_500_view_handler
from assessment.views.utils.treat_feedback_and_resources import treat_resources
from .utils import manage_user_resource, add_last_version_last_assessment_dictionary, add_resources_dictionary

logger = logging.getLogger('monitoring')


class ResourcesView(LoginRequiredMixin, generic.DetailView):
    """ This CBV is used to define the content of the resource page, accessible from the nav bar.
     This page is different from the resource page of the user dashboard although the template is almost the same"""
    model = User
    template_name = 'home/resources.html'
    login_url = 'home:login'
    redirect_field_name = 'home:homepage'

    def get(self, request, *args, **kwargs):
        user = request.user
        self.object = user
        context = self.get_context_data(object=user)

        # Catch the userresources object
        user_resources = manage_user_resource(request)
        if not user_resources:
            error_500_view_handler(request, exception=MultipleObjectsReturned())

        context = add_resources_dictionary(context, user, user_resources)

        context = add_last_version_last_assessment_dictionary(context)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            if "resource_id" in request.POST.dict():
                # The function is defined in assessment/views and add or remove the resource to the user_resource m2m
                # field 'resources'
                return treat_resources(request)
