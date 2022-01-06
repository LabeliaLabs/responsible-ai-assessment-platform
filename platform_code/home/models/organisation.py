from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django.db.models import Q

from .membership import Membership
from .user import User


class Organisation(models.Model):

    TEN = "0-9"
    FIFTY = "10-49"
    HUNDRED = "50-99"
    FIVEHUNDRED = "100-499"
    FIVETHOUSAND = "500-4999"
    PLUS = ">5000"

    SIZE = (
        (TEN, "0-9"),
        (FIFTY, "10-49"),
        (HUNDRED, "50-99"),
        (FIVEHUNDRED, "100-499"),
        (FIVETHOUSAND, "500-4999"),
        (PLUS, ">5000"),
    )

    # I kept the French name as this is already used in production
    LARGE_COMPANY = "Industriel - Grande entreprise"
    MIDSIZE_COMPANY = "Industriel - ETI"
    SMB = "Industriel - PME"
    SOFTWARE_COMPANY = "Prestataire B2B - Editeur de logiciels"
    CONSULTING_AGENCY = "Prestataire B2B - Cabinet de conseil"
    RESEARCH_ORGANISATION = "Organisme de recherche"
    OTHER = "autres"

    SECTOR = (
        (LARGE_COMPANY, _("Industrial - Large company")),
        (MIDSIZE_COMPANY, _("Industrial - Mid-sized company")),
        (SMB, _("Small and Medium-Sized Businesses")),
        (SOFTWARE_COMPANY, _("B2B Service Provider - Software publisher")),
        (CONSULTING_AGENCY, _("B2B service provider - Consulting agency")),
        (RESEARCH_ORGANISATION, _("Research organisation")),
        (OTHER, _("Other")),
    )

    name = models.CharField(max_length=200)
    size = models.CharField(max_length=200, choices=SIZE)
    created_by = models.ForeignKey(
        "home.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_by",
    )
    country = CountryField()  # Set a default country, France
    sector = models.CharField(max_length=1000, choices=SECTOR)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def create_organisation(cls, name, size, country, sector, created_by):
        """
        Create the organisation and the membership which has an admin role
        :param name:
        :param size:
        :param country:
        :param sector:
        :param created_by:
        :return:
        """
        organisation = cls(
            name=name, size=size, country=country, sector=sector, created_by=created_by
        )
        organisation.save()
        Membership.create_membership(
            user=created_by, role="admin", organisation=organisation
        )
        # Give the read_only right to all the platform staff to allow them to see the evaluations
        list_staff_platform = get_list_all_staff_admin_platform()
        for staff_user in list_staff_platform:
            # If the user who created the organisation is admin, it is useless to give him a "read_only" right
            if staff_user != created_by:
                Membership.create_membership(
                    user=staff_user, role="read_only", organisation=organisation, hide_membership=True
                )
        return organisation

    @classmethod
    def get_list_organisations_where_user_as_role(cls, user, role):
        """
        This function is used to obtain the list of organisations the user is member with a defined role
        :return: list of organisations
        """
        return list(
            cls.objects.distinct()
            .filter(membership__user=user, membership__role=role)
            .order_by("-created_at")
        )

    @classmethod
    def get_list_organisations_user_can_edit(cls, user):
        """
        This function returns the list of organisations where the user is member as editor or admin
        Used in security check (when changing evaluations' names)
        :return: list of organisations
        """
        # todo tests
        return list(
            cls.objects.distinct()
            .filter(Q(membership__user=user, membership__role="admin")
                    | Q(membership__user=user, membership__role="editor"))
        )

    def __str__(self):
        return self.name

    def add_user_to_organisation(self, user, role=Membership.ROLES[0][0]):
        """
        Add an user to the organisation, with a defined role (by default read_only)
        :param user: user
        :param role: Membership.ROLE: string, "admin" or "read_only"
        :return: None
        """
        # If the user is not already in the organisation
        if not self.check_user_is_member(user=user):
            Membership.create_membership(user=user, role=role, organisation=self)

    def remove_user_to_organisation(self, user):
        """
        This method removes the user membership of an organisation. This couldn't be used when there is one user in the
        organisation or if the user is not already member of the organisation
        :param user:
        :return:
        """
        if self.count_displayed_members() > 1 and self.check_user_is_member(user):
            membership = self.get_membership_user(user=user)
            membership.delete()

    def get_list_members_not_staff(self):
        """
        Get the list of the members of the organisation (admin, editor or read-only) who
        are not staff of the platform

        Not used anymore in SummaryView to get the list of members
        :return: list
        """
        # List all the members of the organisation (admin, editor or read-only) who are not staff of the platform

        list_members = list(Membership.objects.filter(organisation=self))
        for member in list_members:
            # We need to keep the user if he created the organisation, so he is admin of the organisation
            if member.user.staff and member.role == "read_only":
                list_members.remove(member)
        return list_members

    def get_list_members_to_display(self):
        """
        Get the list of the organisation members which can be displayed (field hide_membership=False)
        to not display staff users which are automatically read_only members
        :return:
        """
        return list(Membership.objects.filter(organisation=self, hide_membership=False))

    def count_displayed_members(self):
        """
        Count the number of member in the organisation, used in the organisation view for the organisation settings
        :return: int
        """
        return len(self.get_list_members_to_display())

    def get_list_admin_members(self):
        """
        Get the list of the admin members of the organisation
        :return: list
        """
        return list(Membership.objects.filter(organisation=self, role="admin"))

    def count_admin_members(self):
        return len(self.get_list_admin_members())

    def get_membership_user(self, user):
        """
        Get the list of the membership of an user to an organisation.
        Normally it is a one element list (the user can only be member once of an organisation for a defined role
        :param user: user in django
        :return: list
        """
        try:
            membership = Membership.objects.get(user=user, organisation=self)
        except (Membership.DoesNotExist, MultipleObjectsReturned):
            membership = None
        return membership

    def check_user_is_member(self, user):
        """
        Check if a user is a member of an organisation. True if he is, else False
        :param user:
        :return: boolean
        """
        membership = self.get_membership_user(user=user)
        return membership is not None

    def get_role_user(self, user):
        """
        Get the role of a user inside an organisation via his membership
        If the user is not member of the organisation
        :param user:
        :return: string
        """
        membership = self.get_membership_user(user=user)
        if membership is not None:
            return membership.role

    def check_user_is_member_as_admin(self, user):
        """
        Check if the user is member AND member as admin. If he is, return True, else False
        :param user: user
        :return: boolean
        """
        membership = self.get_membership_user(user=user)
        if membership is not None:
            return membership.role == "admin"
        else:
            return False

    def check_user_is_member_and_can_edit_evaluations(self, user):
        membership = self.get_membership_user(user=user)
        if membership is not None:
            return membership.role == "admin" or membership.role == "editor"
        else:
            return False

    def get_list_evaluations(self):
        """
        Return the list of the evaluations for the organisation
        :return:
        """
        return list(self.evaluation_set.all().order_by("-created_at"))

    def get_list_assessment_version(self):
        """
        Return the list of the versions as string that the organisation has
        :return:
        """
        list_eval = self.get_list_evaluations()
        list_version = []
        if list_eval:
            for eval in list_eval:
                version = eval.assessment.version
                if version not in list_version:
                    list_version.append(eval.assessment.version)
        return list_version

    def get_last_assessment_version(self):
        """
        Return the float of the latest version of the assessment present in the orga
        :return: float or None
        """
        list_version = self.get_list_assessment_version()
        if list_version:
            return max([float(i) for i in list_version])
        else:
            return None

    def count_evaluations_finished_or_not(self, finished=True):
        """
        Count the number of evaluations finished if finished=True, else in progress
        """
        # todo tests
        # todo use it in orga-evaluation.html instead of template tag
        count = 0
        for evaluation in self.get_list_evaluations():
            if finished:
                if evaluation.is_finished:
                    count += 1
            else:
                if not evaluation.is_finished:
                    count += 1
        return count


def get_list_all_staff_admin_platform():
    """
    This function returns the list of all the admin or staff users (an admin has necessarily the field 'staff'=True)
    :return: list of users
    """
    return list(User.object.filter(staff=True))
