import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q
from django.shortcuts import redirect
from django.views import generic

from assessment.forms import EvaluationMutliOrgaForm, EvaluationForm
from assessment.models import Evaluation, EvaluationElement
from assessment.views.utils.edit_evaluation_name import treat_evaluation_name_edition
from assessment.views.utils.error_handler import (
    error_500_view_handler,
    error_400_view_handler,
)
from assessment.views.utils.treat_feedback_and_resources import treat_resources
from assessment.views.utils.utils import (
    manage_evaluation_max_points,
    manage_evaluation_score,
    treat_evaluation_creation_valid_form,
    treat_delete_note, manage_missing_language,
)
from home.forms import OrganisationCreationForm
from home.models import User, Membership
from .utils import (
    organisation_creation,
    manage_user_resource,
    add_last_version_last_assessment_dictionary,
    add_resources_dictionary,
)

logger = logging.getLogger("monitoring")


class ProfileView(LoginRequiredMixin, generic.DetailView):
    model = User
    template_name = "home/profile.html"
    login_url = "home:login"
    redirect_field_name = "home:homepage"
    context = {}

    def get(self, request, *args, **kwargs):

        user = request.user
        self.object = user
        self.context = self.get_context_data(object=user)

        # Catch the user_resources object
        user_resources = manage_user_resource(request)
        if not user_resources:
            error_500_view_handler(request, exception=MultipleObjectsReturned())

        # Add resources to context
        self.context = add_resources_dictionary(self.context, user, user_resources)

        self.add_organisation_list_context(user)

        # Get the evaluations created by the user
        # This can be modified if we want all the evaluations of the organisations the user belong to
        # Can be empty
        self.add_evaluations_context(user)
        for evaluation in self.context['evaluations']:
            manage_missing_language(request, evaluation)
        # Get user notes on evaluations from the organizations to which the user belongs
        self.add_notes_context(user)

        # If the scoring system has changed, it set the max points again for the evaluation, sections, EE
        success_max_points = manage_evaluation_max_points(
            request=request, evaluation_list=self.context["evaluations"]
        )
        if not success_max_points:
            return redirect("home:user-profile")

        self.context["evaluation_score_dic"] = manage_evaluation_score(
            request=request, evaluation_list=self.context["evaluations"]
        )
        self.context["new_orga_form"] = OrganisationCreationForm(
            prefix="organisation-creation"
        )
        self.context["new_evaluation_form"] = EvaluationMutliOrgaForm(
            user=user, prefix="evaluation-creation"
        )

        self.context = add_last_version_last_assessment_dictionary(self.context)
        return self.render_to_response(self.context)

    def post(self, request, *args, **kwargs):
        """
        Manage the different forms there are in this view (organisation creation and evaluation creation).
        The way this is manage can be improved but currently it is working. We check if there are key words of
        each form in the request.POST dictionary
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.method == "POST":
            user = request.user
            # Differentiate between the organisation creation and the evaluation creation
            # It could be done with the form id but easier this way, may be to improve
            # If organisation-creation-name, it means it is the organisation creation form, else evaluation creation
            if "organisation-creation-name" in request.POST:
                # create a form instance and populate it with data from the request:
                form = OrganisationCreationForm(
                    request.POST, prefix="organisation-creation"
                )
                # check whether it's valid:
                if form.is_valid():
                    organisation = organisation_creation(request, form)
                    response = redirect("assessment:orga-summary", organisation.id)
                    return response
                else:
                    return self.form_invalid(form)

            # If there is "organisation" in the form, it is a Evaluation creation form
            elif "evaluation-creation-name" in request.POST:

                # If the user belongs to multiple organisation, it is a form with a field organisation
                if (
                    len(user.get_list_organisations_where_user_as_role(role="admin"))
                    >= 1
                    or len(
                        user.get_list_organisations_where_user_as_role(role="editor")
                    )
                    >= 1
                ):
                    form = EvaluationMutliOrgaForm(
                        request.POST, user=user, prefix="evaluation-creation"
                    )
                    if form.is_valid():
                        return treat_evaluation_creation_valid_form(
                            form, form.cleaned_data.get("organisation"), user
                        )
                    else:
                        # TODO treat invalid form
                        return redirect("home:orga-creation")

                # Case the user doesn't belong to an organisation as admin, he shouldn t be able to create an evaluation
                # So we redirect to organisation creation
                else:
                    return redirect("home:orga-creation")

            # If resource id in the post, the user unliked a resource from his resource liked page
            # Or if the ajax if when the user likes/unlikes a resource
            elif "resource_id" in request.POST.dict():
                # The function is defined in assessment/views and add or remove the resource to the user_resource m2m
                # field 'resources'
                return treat_resources(request)

            # If the user edits the name of the evaluation
            elif (
                "name" in request.POST.dict() and "evaluation_id" in request.POST.dict()
            ):
                return treat_evaluation_name_edition(request)

            elif "note_element_id" in request.POST.dict():
                return treat_delete_note(request)

            # Case there is a post which is not managed by the function
            else:
                logger.error(
                    "[post_error] The post in ProfilView is not managed by any case."
                )
                error_400_view_handler(request)

    def add_organisation_list_context(self, user):
        """
        Add the organisations the user is member (read_only, edit, or admin role).
        They will be displayed in the organisation cards.
        """
        # Get the organisations where the user is member to
        organisation_list = []
        # Can be empty query
        query_membership = Membership.objects.filter(
            user=user
        )  # Possibility to add a condition on the role

        for membership in query_membership:
            organisation_list.append(membership.organisation)
        self.context["organisations"] = organisation_list

    def add_evaluations_context(self, user):
        """
        Add the evaluations where the user is member as editor or administrator.
        He will be able to see them in his profile view.
        """
        list_evaluations = Evaluation.objects.filter(
            Q(
                organisation__membership__user=user,
                organisation__membership__role="admin",
            )
            | Q(
                organisation__membership__user=user,
                organisation__membership__role="editor",
            )
        )

        self.context["evaluations"] = sorted(
            list(list_evaluations), key=lambda x: x.created_at, reverse=True
        )
        self.context["evaluation_form_dic"] = {}
        for evaluation in list_evaluations:
            self.context["evaluation_form_dic"][str(evaluation.id)] = EvaluationForm(
                name=evaluation.name, auto_id=False
            )

    def add_notes_context(self, user):
        """
        Add to context a dictionary with all evaluation -> section -> element -> notes where the element has notes and
        the evaluation belong to an organisation that the user is editor or admin of.
        These notes will be displayed on profileView
        """
        elements = (
            EvaluationElement.objects.exclude(user_notes__isnull=True)
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
            .order_by("id")
        )
        user_notes_dict = {}
        for element in elements:
            section = element.section
            evaluation = section.evaluation
            if evaluation not in user_notes_dict:
                user_notes_dict[evaluation] = {}
            if section not in user_notes_dict[evaluation]:
                user_notes_dict[evaluation][section] = {}
            user_notes_dict[evaluation][section][
                element
            ] = element.user_notes
        self.context["user_notes_dict"] = user_notes_dict
