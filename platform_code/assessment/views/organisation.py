import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView
from django.conf import settings

from assessment.forms import EvaluationForm
from assessment.forms_.member_forms import AddMemberForm, EditRoleForm
from assessment.models import Evaluation
from assessment.views.utils.security_checks import (
    membership_security_check,
    can_edit_security_check,
    membership_admin_security_check,
)
from assessment.views.utils.utils import (
    manage_evaluation_max_points,
    manage_evaluation_score,
    treat_evaluation_creation_valid_form,
)
from assessment.templatetags.assessment_tags import get_sector_as_str
from home.forms import OrganisationEditionForm
from home.models import Organisation, User, Membership, PendingInvitation
from home.views.utils import add_last_version_last_assessment_dictionary

logger = logging.getLogger('monitoring')


def leave_organisation(request, **kwargs):
    """
    This function is used when user wants to leave an organisation
    :param request:
    :param args:
    :param kwargs:
    :return:
    """
    user = request.user
    organisation_id = kwargs.get("orga_id")
    organisation = get_object_or_404(
        Organisation, id=organisation_id
    )  # Get 404 if orga_id doesn't exist
    # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
    if not membership_security_check(request, organisation=organisation):
        return redirect("home:homepage")
    try:
        member = organisation.get_membership_user(user=user)
    except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError) as e:
        logger.warning(f"[member_issue] The user {user.email} wants to leave the organisation {organisation.name},"
                       f"id {organisation_id} but the query to get the membership failed, error {e}")
        messages.warning(request, _("An issue occurred."))
        member = None
    if member:
        # If the user is the only admin member (it should not happen except if both user do the action without refresh
        if member.role == "admin" and organisation.count_admin_members() == 1:
            messages.warning(request, _("You cannot leave the organisation %(organisation_name)s because you are"
                                        " the unique admin member.") % {"organisation_name": organisation.name})
            logger.info(f"[user_left_organisation_refused] The user {user.email} wanted to leave the organisation "
                        f"{organisation.name} (id {organisation.id}) but he cannot because he is the only admin.")
            return redirect("assessment:orga-summary", organisation_id)
        else:
            # A staff member does not really leave the organisation but become hidden and read_only member
            if member.user.staff:
                member.role = "read_only"
                member.hide_membership = True
                member.save()
            else:
                member_role = member.role
                member.delete()
                logger.info(f"[user_left_organisation] The user {user.email} left the organisation {organisation.name} "
                            f"(id {organisation.id}) in which he was member as {member_role}.")
            messages.success(request, _("You are no longer member of the organisation %(organisation_name)s.") % {
                "organisation_name": organisation.name
            })
    return redirect("home:user-profile")


class SummaryView(LoginRequiredMixin, DetailView):
    model = Organisation
    template_name = "assessment/organisation/organisation.html"
    form_class = EvaluationForm
    login_url = "home:login"
    redirect_field_name = "home:homepage"
    context = {}
    data_update = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_update = {"success": False, "message": _("An error occurred.")}

    def get(self, request, *args, **kwargs):
        """
        This get manages the context for the organisation view which has 3 tabs:
            - the evaluation tab with data on the evaluations with forms to edit name and delete
            - the member tab with data on the members and the forms to add, edit or remove some and to
            leave the organisation
            - the organisation settings with data on the organisation (no form yet to delete the organisation TODO)
        """
        # Get the organisation from the url
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the organisation (caught in the url), if not, return HttpResponseForbidden
        if not membership_security_check(request, organisation=organisation):
            return redirect("home:homepage")

        self.object = organisation
        self.context = self.get_context_data(object=self.object)
        self.context["organisation"] = organisation

        # Add evaluations to the context
        self.add_evaluation_list_to_context(organisation)

        # If the scoring system has changed, it set the max points again for the evaluation, sections, EE
        success_max_points = \
            manage_evaluation_max_points(request=request, evaluation_list=self.context["evaluation_list"])
        if not success_max_points:
            return redirect("home:user-profile")

        # Process the evaluation score if needed for each evaluation
        self.context["evaluation_score_dic"] =\
            manage_evaluation_score(request=request, evaluation_list=self.context["evaluation_list"])

        self.context["form"] = EvaluationForm()

        self.context["edit_organisation_form"] = OrganisationEditionForm(organisation=organisation,
                                                                         prefix="edit-organisation")
        # Add all the information for member management (forms, member list, etc)
        self.add_member_data_and_forms_to_context(organisation)

        # The last assessment created is necessarily the last version as it must be strictly croissant
        self.context = add_last_version_last_assessment_dictionary(self.context)
        return self.render_to_response(self.context)

    def add_evaluation_list_to_context(self, organisation):
        """
        Add the list of evaluations for this organisation to the context
        """
        self.context["evaluation_list"] = \
            list(Evaluation.objects.filter(organisation=organisation).order_by("-created_at"))

    def add_member_data_and_forms_to_context(self, organisation):
        """
        Manage the member information to add to the context
        """
        self.context["add_member_form"] = AddMemberForm(auto_id=False)
        self.context["member_list"] = organisation.get_list_members_to_display()
        self.context["pending_member_list"] = organisation.get_pending_list()
        # Dictionary of forms to edit the role of members of the organisation
        self.context["edit_member_role_form_dic"] = {}
        for member in self.context["member_list"]:
            self.context["edit_member_role_form_dic"][str(member.id)] = EditRoleForm(member=member, auto_id=False)
        # Dictionary of the forms to edit the role of the invitations sent to join the organisation
        self.context["edit_invitation_role_form_dic"] = {}
        for invitation in self.context["pending_member_list"]:
            self.context["edit_invitation_role_form_dic"][str(invitation.id)] = EditRoleForm(invitation=invitation,
                                                                                             auto_id=False)

    def post(self, request, **kwargs):
        """
        POST which manages 4 cases:
            - evaluation name modification with a form (evaluation tab)
            - add a member or send an invitation with ajax (member tab)
            - edit a role of a member or invitation with ajax (member tab)
            - delete an invitation or remove a member not admin with ajax (member tab)
        """
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)
        # Check if the user is member of the orga, if not, return HttpResponseForbidden
        if not membership_security_check(request, organisation=organisation):
            return redirect('home:homepage')

        # Check if the user is an admin/edit member of the orga, if not, return to the same page
        if not can_edit_security_check(request, organisation=organisation):
            messages.warning(request, _("You don't have the right to do this action."))
            return redirect("assessment:orga-summary", organisation.id)
        if request.method == "POST":
            user = request.user

            # case it is an evaluation creation
            if "name" in request.POST and not request.is_ajax():
                # create a form instance and populate it with data from the request:
                form = EvaluationForm(request.POST)
                # check whether it's valid:
                if form.is_valid():
                    return treat_evaluation_creation_valid_form(form, organisation, user)

            # Case there are actions on the members with ajax post methods
            # These actions are only possible with "admin" role
            if request.is_ajax():

                if not membership_admin_security_check(request, organisation=organisation):
                    self.data_update["message"] = _("You don't have the right to do this action.")
                    messages.warning(request, _("You don't have the right to do this action."))
                    return HttpResponse(json.dumps(self.data_update), content_type="application/json")

                # Case the user wants to add another member to the organisation
                if "email" in request.POST:
                    self.treat_add_member(request, organisation, user)

                # Case an admin member wants to remove another user which should not be admin member
                # Check user is member with admin role already done
                elif "remove_member_id" in request.POST:
                    self.treat_remove_user(request, organisation, user)

                # Case the user wants to remove an invitation to join the organisation
                elif "delete_invitation_id" in request.POST:
                    self.treat_delete_invitation(request, organisation, user)

                # If the user edit the role of another member (which cannot be an admin member)
                elif "edit_member_id" in request.POST:
                    self.treat_edit_membership_role(request, organisation, user)

                elif "edit_invitation_id" in request.POST:
                    self.treat_edit_invitation_role(request, organisation, user)

                elif "edit-organisation-name" in request.POST:
                    self.treat_edit_organisation(request, organisation, user)
                return HttpResponse(json.dumps(self.data_update), content_type="application/json")

    def treat_add_member(self, request, organisation, user):
        """
        Treat the user action to add a user (based on email address) to the organisation, with different cases
        whether the user is staff of the platform or not and whether the email address is linked to an existing account
        or not. If not, an invitation to create an account is sent and the futur user will automatically join the
        organisation.
        """
        form = AddMemberForm(request.POST)
        if form.is_valid():
            email_address = form.cleaned_data.get("email")
            role = form.cleaned_data.get("role")
            list_user_invited = list(User.object.filter(email=email_address))
            if len(list_user_invited) == 1:
                user_invited = list_user_invited[0]

                # Check if the user is already a member, in this case, the role just need to be edited
                if organisation.check_user_is_member(user=user_invited) and not user_invited.staff:
                    logger.warning(f"[add_member_failed] Invitation to join an organisation failed, "
                                   f"the user invited {user_invited.email} is already member of the "
                                   f"organisation {organisation.name} with the role "
                                   f"{organisation.get_role_user(user_invited)}")
                    self.data_update["message"] = _("The user is already member. Please, "
                                                    "edit his rights instead.")
                # Case the user is STAFF so normally he has already a membership in the organisation
                # with role "read_only", except if he left it
                if user_invited.staff:
                    self.add_staff_user_to_the_organisation(organisation, user, user_invited, role)

                # Case the user exists and he his not a member of the organisation
                if not organisation.check_user_is_member(user=user_invited) and not user_invited.staff:
                    self.add_user_to_the_organisation(organisation, user, user_invited, role)

            # Case the user invited has not an account, so we sent an email to the user and we create a
            # pending membership
            # No token or uid required as the link is just a link to signup
            elif len(list_user_invited) == 0:
                self.send_invitation_to_join_organisation(request, organisation, user, email_address, role)
        # Invalid form
        else:
            self.data_update["message"] = _("Please enter a valid email.")

    def add_staff_user_to_the_organisation(self, organisation, user, user_invited, role):
        """
        Actions to add a staff user to the organisation
        """
        # if the staff user is already member of the organisation but the other members are not
        # aware of this, just edit his role and change hide_membership
        if organisation.get_membership_user(user_invited):
            membership_user_invited = organisation.get_membership_user(user_invited)
            membership_user_invited.role = role
            membership_user_invited.hide_membership = False
            membership_user_invited.save()
        # the staff user left the organisation
        else:
            Membership.create_membership(user=user_invited,
                                         organisation=organisation,
                                         role=role,
                                         hide_membership=False)
        self.messages_user_added(organisation, user, user_invited, role)

    def add_user_to_the_organisation(self, organisation, user, user_invited, role):
        """
        Actions to add a user user_invited to the organisation
        """
        Membership.create_membership(user=user_invited,
                                     organisation=organisation,
                                     role=role)
        self.messages_user_added(organisation, user, user_invited, role)

    def messages_user_added(self, organisation, user, user_invited, role):
        """
        Manage messages to the user and logs when a user is added to an organisation
        """
        logger.info(f"[add_member_organisation] The user {user.email} has invited "
                    f"{user_invited.email} to join the organisation {organisation.name} "
                    f"(id {organisation.id}) with the role {role}")
        self.data_update["message"] = _("The user has been added to the organisation.")
        self.data_update["success"] = True
        # Be careful if the structure of the array changes
        self.data_update["data_user"] = {"0": user_invited.get_full_name(),
                                         "1": user_invited.email,
                                         "2": role,
                                         "3": ""}  # User can not already have created evaluations

    def send_invitation_to_join_organisation(self, request, organisation, user, email_address, role):
        """
        Actions to send an invitation to create an account and add pending invitation to join the organisation
        """
        current_site = get_current_site(request)
        mail_subject = _("Substra - Invitation to join an organisation")

        message = render_to_string('assessment/organisation/member/add-member-email.html', {
            'user': user,
            'organisation': organisation,
            'domain': current_site.domain,
            'protocol': "http" if settings.DEBUG else "https",
        })
        email = EmailMessage(mail_subject, message, to=[email_address])
        email.send()
        PendingInvitation.create_pending_invitation(email=email_address, organisation=organisation, role=role)
        self.messages_invitation_send(request, organisation, email_address, role)

    def messages_invitation_send(self, request, organisation, email_address, role):
        """
        Manage the messages when an invitation to create an account and join the organisationis sent
        """
        self.data_update["success"] = True
        self.data_update["data_user"] = {"0": email_address,
                                         "1": email_address,
                                         "2": role + " (pending)",
                                         "3": ""}
        self.data_update["message"] = _("The user does not yet have an account on the platform. "
                                        "An invitation has been sent to him.")
        logger.info(f"[add_member_invitation_sent] The user {request.user.email} has sent an email "
                    f" invitation to {email_address} to join the organisation (id {organisation.id})"
                    f" with the role '{role}'")

    def treat_remove_user(self, request, organisation, user):
        """
        Treat the case the user wants to remove a member of the organisation.
        It cannot be an admin member.
        """
        member = get_object_to_action(request, organisation, user, Membership, "member", "remove")
        if member:
            # An admin member cannot be removed from the organisation, normally no button to remove
            if not member.role == "admin" and member.organisation == organisation:
                member_deleted_email = member.user.email
                # If the user is staff of the platform, it is not deleted but hidden and set to "read_only"
                if member.user.staff:
                    member.hide_membership = True
                    member.role = "read_only"
                    member.save()
                # If the user is not staff, we just delete its membership
                else:
                    member.delete()
                    logger.info(f"[member_removed] The user {user.email} removed the membership of the user"
                                f" {member.user.email} from the organisation {organisation.name} (id "
                                f"{organisation.id})")
                # In both cases we tell the user it succeeded
                self.data_update["success"] = True
                self.data_update["message"] = _("The user %(member_deleted_email)s is no longer a member of the "
                                                "organisation and cannot access to it.") % {
                                                "member_deleted_email": member_deleted_email
                                                }
            # Member is an admin member
            else:
                self.data_update["message"] = _("You cannot remove an admin member from the organisation.")

    def treat_delete_invitation(self, request, organisation, user):
        """
        Treat the case the user deletes an invitation sent to join the organisation
        """
        invitation = get_object_to_action(request, organisation, user, PendingInvitation, "invitation", "delete")
        if invitation:
            invitation_deleted_email = invitation.email
            invitation.delete()
        self.data_update["success"] = True
        self.data_update["message"] = _("The invitation to %(invitation)s has been deleted.") % {
            "invitation": invitation_deleted_email
        }
        logger.info(f"[invitation_deleted] The user {user.email} deleted the invitation for the email"
                    f" {invitation.email} to join the organisation {organisation.name} (id "
                    f"{organisation.id})")

    def treat_edit_membership_role(self, request, organisation, user):
        """
        Treat the case when the user edits the role of another member (not admin)
        """
        member = get_object_to_action(request, organisation, user, Membership, "member", "edit", hide_membership=False)
        if member:
            # An admin member cannot have his role changed, normally no button to edit
            if not member.role == "admin" and member.organisation == organisation:
                new_role = request.POST.get("role")  # role or None
                # Check that the new role is a role defined by the class Membership
                if Membership.check_role(new_role):
                    former_role = member.role
                    member.role = new_role
                    member.save()
                    self.data_update["new_role"] = new_role
                    self.data_update["success"] = True
                    self.data_update["message"] = _("The user %(member_email)s has now the %(new_role)s "
                                                    "rights in the organisation.") % {
                                                    "member_email": member.user.email,
                                                    "new_role": new_role
                                                    }
                    logger.info(f"[member_role_edited] The user {user.email} edited the role of the user"
                                f" {member.user.email}, from {former_role} to {new_role} in the "
                                f"organisation {organisation.name} (id {organisation.id})")
                # Role is not a valid one
                else:
                    logger.warning(f"[member_role_edited_error] The user {user.email} tried to edit the "
                                   f"role of the user {member.user.email}, from {member.role} to {new_role}"
                                   f" which not a valid one, "
                                   f"in the organisation {organisation.name} (id {organisation.id})")
            else:
                self.data_update["message"] = _("You cannot change the rights of an admin member.")

    def treat_edit_invitation_role(self, request, organisation, user):
        """
        Treat the case when the user edits the role of an invitation sent
        """
        invitation = get_object_to_action(request, organisation, user, PendingInvitation, "invitation", "edit")
        if invitation:
            new_role = request.POST.get("role")  # role or None
            # Check that the new role is a role defined by the class Membership
            if Membership.check_role(new_role):
                former_role = invitation.role
                invitation.role = new_role
                invitation.save()
                self.data_update["new_role"] = new_role + " (pending)"
                self.data_update["success"] = True
                self.data_update["message"] = _("The invitation to %(invitation_email)s to join the"
                                                " organisation"
                                                " is now with the %(new_role)s rights in the"
                                                " organisation.") % {
                                                  "invitation_email": invitation.email,
                                                  "new_role": new_role
                                              }

                logger.info(f"[invitation_role_edited] The user {user.email} edited the role of the "
                            f"invitation to {invitation.email} to join the organisation {organisation.name}"
                            f"(id {organisation.id}), from {former_role} to {new_role},")
            # Role is not a valid one
            else:
                logger.warning(f"[invitation_role_edited_error] The user {user.email} tried to edit the "
                               f"role of the invitation to {invitation.email}, from {invitation.role} to "
                               f"{new_role} which not a valid one, "
                               f"in the organisation {organisation.name} (id {organisation.id})")

    def treat_edit_organisation(self, request, organisation, user):
        form = OrganisationEditionForm(request.POST, prefix="edit-organisation")
        if form.is_valid():
            name = form.cleaned_data.get("name")
            size = form.cleaned_data.get("size")
            country = form.cleaned_data.get("country")
            sector = form.cleaned_data.get("sector")
            organisation.name = name
            organisation.size = size
            organisation.country = country
            organisation.sector = sector
            sector_displayed = get_sector_as_str(sector)
            organisation.save()
            self.data_update["organisation_name"] = _("Name:") + " " + name
            self.data_update["organisation_name_only"] = name
            self.data_update["organisation_size"] = _("Size:") + " " + size
            self.data_update["organisation_country"] = _("Country:") + " " + country
            self.data_update["organisation_sector"] = _("Sector:") + " " + sector_displayed
            logger.info(f"[organisation_edited] The user {user}, with the role {organisation.get_role_user(user)},"
                        f"edited the information of the organisation {str(organisation)}")
            self.data_update["message"] = _("The organisation information has been updated.")
            self.data_update["message_type"] = "alert-success"
            self.data_update["success"] = True
        else:
            self.data_update["message"] = _("An error occurred, please verify the data you entered.")
            self.data_update["message_type"] = "alert-danger"
            self.data_update["success"] = False


def get_object_to_action(request, organisation, user, object_class, object_name, action, **kwargs):
    """
    This function gets the object of the class object_class in the data base if it exists and is unique, else
    return None and create a log

    :param request: request
    :param organisation: organisation
    :param user: user who did the action
    :param object_class: class in which the object exists (Membership, PendingInvitation)
    :param object_name: string ("member", invitation")
    :param action: string (action to realise "delete", "remove", "edit")
    :param kwargs: dictionary which can add precision for the query (be careful to have a correct query)

    :returns: object_, the object get in the DB
    """
    object_id = request.POST.get(f"{action}_{object_name}_id")
    try:
        object_ = object_class.objects.get(id=object_id, organisation=organisation, **kwargs)
    except (MultipleObjectsReturned, ObjectDoesNotExist, ValueError) as e:
        logger.warning(f"[{object_name}_{action}_error] The user {user.email} wants to {action} the "
                       f"{object_name} with id {object_id} of the organisation {organisation.name}"
                       f" (id {organisation.id}) but there is an error with the query, error {e}")
        object_ = None
    return object_
