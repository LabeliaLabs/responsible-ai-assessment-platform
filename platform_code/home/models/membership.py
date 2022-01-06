from django.db import models
from django.utils.translation import gettext_lazy as _


class Membership(models.Model):
    """
    The class Membership

    ADMIN manages the evaluations and the members of the organisation
    EDITOR manages the evaluations (creation edit and delete with conditions) of the organisation
    READ_ONLY can only consult the evaluations
    """

    ADMIN = "admin"
    READ_ONLY = "read_only"
    EDITOR = "editor"

    ROLES = (
        (READ_ONLY, _("read only")),
        (EDITOR, _("editor")),
        (ADMIN, "admin"),
    )

    user = models.ForeignKey("home.User", on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        "home.Organisation", blank=True, null=True, on_delete=models.CASCADE
    )
    role = models.CharField(max_length=200, choices=ROLES, default=ADMIN)
    hide_membership = models.BooleanField(default=False)

    @classmethod
    def create_membership(cls, user, organisation, role, hide_membership=False):
        if cls.check_role(role):
            member = cls(user=user, organisation=organisation, role=role, hide_membership=hide_membership)
            member.save()

    @classmethod
    def create_membership_pending_invitations(cls, user):
        """
        For a user, create all the membership objects which was pending
        This is used when the user creates his account on the platform
        :param user: user
        :return:
        """
        # Get all the invitations for the user address email
        list_pending_invitations = PendingInvitation.get_list_pending_invitation(user)
        for invitation in list_pending_invitations:
            organisation = invitation.organisation
            # Check if user is not already member of the organisation (should not happen)
            if not organisation.check_user_is_member(user):
                cls.create_membership(user, organisation, role=invitation.role)
                invitation.delete()

    @classmethod
    def check_role(cls, role_to_check):
        """
        Check that a string 'role_to_check' is a defined role (always check the 1st value of the tuple of ROLES)
        Do not use French version ('editeur', 'lecteur' in the code)
        :param role_to_check: string
        :return:
        """
        list_roles = [cls.ROLES[i][0] for i in range(len(cls.ROLES))]
        return role_to_check in list_roles

    @classmethod
    def get_list_all_memberships_user(cls, user):
        """
        Get the list of all the membership of an user
        :return: list of memberships
        """
        return list(cls.objects.filter(user=user))

    def __str__(self):
        return str(self.user) + " in " + str(self.organisation) + " (" + self.role + ")"


class PendingInvitation(models.Model):
    """
    The PendingInvitation class is used to manage the invitations on organisations when the user has no account
    on the platform. The information of the invitation are stored in this class (email address, role, organisation)

    When a user creates an account, we check if his email address has pending invitations. If yes, merberships are
    created for the user in the organisations with the defined role. After the creation, the invitation are destroyed

    """

    email = models.EmailField(unique=False)
    organisation = models.ForeignKey("home.Organisation", on_delete=models.CASCADE)
    role = models.CharField(max_length=255)

    @classmethod
    def create_pending_invitation(cls, email, organisation, role):
        if Membership.check_role(role):
            invitation = cls(email=email, organisation=organisation, role=role)
            invitation.save()

    @classmethod
    def get_list_pending_invitation(cls, user):
        """
        :return: list of pending invitations
        """
        return list(cls.objects.filter(email=user.email))

    @classmethod
    def get_organisation_pending_list(cls, organisation):
        """
        This method returns the list of the pending invitations to join the organisation
        This is used to create rows for pending user invitations of the member array in orga-members.html
        :return: list of dictionaries
        """
        return list(cls.objects.filter(organisation=organisation))

    def __str__(self):
        return "Invitation for "+self.email+" in the organisation "+self.organisation.name+" with the role "+self.role
