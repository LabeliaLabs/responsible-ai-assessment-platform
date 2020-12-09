import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView

from assessment.models import Evaluation
from assessment.utils import get_client_ip
from assessment.views.utils.security_checks import membership_security_check
from assessment.views.utils.utils import (
    manage_evaluation_max_points,
    manage_evaluation_score,
    set_form_for_results
)
from home.models import Organisation

logger = logging.getLogger('monitoring')


class ResultsView(LoginRequiredMixin, DetailView):
    """
    This view define the page of the results of an evaluation, with the score and the overall evaluation and choices
    It is accessible only if the evaluation is finished.
    """
    model = Evaluation
    template_name = "assessment/results.html"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)

        # Check if the user is member of the org, if not, return HttpResponseForbidden
        if not membership_security_check(request, organisation=organisation):
            return redirect('home:homepage')

        evaluation = get_object_or_404(Evaluation, id=kwargs.get("pk"), organisation=organisation)

        # If the evaluation is finished, which should always be the case here, set the score of the evaluation
        if evaluation.is_finished:

            # Check on that the "pk" in kwargs is linked with the organisation done 4 lines above
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)

            # If the scoring system has changed, it set the max points again for the evaluation, sections, EE
            success_max_points = manage_evaluation_max_points(request=request, evaluation_list=[evaluation])
            if not success_max_points:
                return redirect("home:user-profile")

            # Get the score and calculate it if needed
            evaluation_score_dic = manage_evaluation_score(request=request, evaluation_list=[evaluation])
            if evaluation_score_dic[evaluation.id]:
                context["evaluation_score"] = evaluation_score_dic[evaluation.id]
            # Error to get the score, the score is None so redirection
            else:
                return redirect("home:user-profile")

            context["dic_form_results"] = set_form_for_results(evaluation=evaluation)
            context["section_list"] = list(evaluation.section_set.all().order_by("master_section__order_id"))
            context["evaluation_element_list"] = evaluation.get_list_all_elements()
            context["organisation"] = organisation
            return self.render_to_response(context)
        else:
            logger.warning(f"[html_forced] The user {request.user.email}, with IP address {get_client_ip(request)} "
                           f"forced the button to valid the evaluation"
                           f" (id {evaluation.id}) to access the results")
            messages.warning(request, _("You cannot do this action!"))
            return redirect("home:user-profile")