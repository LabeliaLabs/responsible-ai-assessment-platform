from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django.conf import settings


# In this model file, the user authentication system is completed to add the fact that a user is part of an
# organisation.
# A user is define by a username and email address. It s what the user will see when he wants to login
# (and his password)
# But a user can belong to multiple organisations through different memberships. This table Membership is used to
# create this relation. For example, for a user which belongs to 2 organisations, there will be 2 lines in the
# membership table, one with the user_id, organisation 1 id and the user role in this organisation, and the other
# with the same user_id, the organisation 2 id and the role of the user in this second organisation
# On the other side, for an organisation, it has multiple members
# Admin members of an orga can edit, add, delete members to the orga (if they are not already membership.role = admin
# of the orga) to avoid
# Admin members can not delete an orga if there are other members in the orga (see if only other admin member)


class PlatformManagement(models.Model):
    """
    This class aims to furnish the possibility to admin users to realize actions on the platform globally.
    The platform_update fields manage the fact that during the release on production, the users may lose the unsaved
    content so a banner is displayed.
    The activate_multi_languages field manages the fact that we may want to do not activate the English version of the
    platform (because English assessment is not imported).
    """
    # Manage delivery and add a banner on the site
    platform_update = models.BooleanField(default=False)
    delivery_text_en = models.TextField(max_length=1000, default="Platform update ongoing")
    delivery_text_fr = models.TextField(max_length=1000, default="Mise à jour de la plateforme en cours")
    # Manage the language
    activate_multi_languages = models.BooleanField(default=False, help_text="This should not be activated if an "
                                                                            "assessment does not exist both in French "
                                                                            "and English")

    def __str__(self):
        return "Platform management"

    @classmethod
    def get_or_create(cls):
        """"
        Get the object if it exists or creates it and return it
        """
        if cls.objects.first():
            return cls.objects.first()
        else:
            created_obj = cls()
            created_obj.save()
            return created_obj


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError(_("Users must have an email address"))

        user = self.model(email=self.normalize_email(email),)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(email, password=password,)
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(email, password=password,)
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Create the class User, using the email instead of the username

    Note that I tried to use the same syntax with is_active instead of active but I couldn't do the migration with this
    case, the field wasn't caught. This issue forced me to overwrite some methods and class to reset the user password.

    """
    languages = settings.LANGUAGES

    email = models.EmailField(
        verbose_name="email",
        max_length=255,
        unique=True,
        error_messages={"unique": _("A user with that email already exists.")},
    )
    # TODO replace fields active, admin, staff by is_admin, is_active, is_staff and delete the modification in
    #  PasswordResetForm (in home/forms) and PasswordReset (in home/views)
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)  # a admin user; non super-user
    admin = models.BooleanField(default=False)  # a superuser
    created_at = models.DateTimeField(default=timezone.now)
    language_preference = models.CharField(default="fr", choices=languages, max_length=5)
    # notice the absence of a "Password field", that is built in.

    object = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email & Password are required by default.

    def get_email(self):
        # The user is identified by their email address
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def get_language_preference(self):
        return self.language_preference

    def __str__(self):  # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return self.active and self.admin

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return self.active and self.admin

    def get_all_data(self):
        """This function is used to download the personal data of the user. It returns a dictionary."""
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        return self.staff

    @property
    def is_admin(self):
        """Is the user a admin member?"""
        return self.admin

    @property
    def is_active(self):
        """Is the user active?"""
        return self.active

    def get_list_all_memberships_user(self):
        """
        Get the list of all the membership of an user
        :return: list of memberships
        """
        return list(Membership.objects.filter(user=self))

    def get_list_organisations_where_user_as_role(self, role):
        """
        This function is used to obtain the list of organisations the user is member with a defined role
        :return: list of organisations
        """
        return list(
            Organisation.objects.distinct()
            .filter(membership__user=self, membership__role=role)
            .order_by("-created_at")
        )

    def get_list_organisations_user_can_edit(self):
        """
        This function returns the list of organisations where the user is member as editor or admin
        Used in security check (when changing evaluations' names)
        :return: list of organisations
        """
        # todo tests
        return list(
            Organisation.objects.distinct()
            .filter(Q(membership__user=self, membership__role="admin")
                    | Q(membership__user=self, membership__role="editor"))
        )

    def get_list_pending_invitation(self):
        """
        :return: list of pending invitations
        """
        return list(PendingInvitation.objects.filter(email=self.email))


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
        if organisation in Organisation.objects.all() and Membership.check_role(role):
            invitation = cls(email=email, organisation=organisation, role=role)
            invitation.save()

    def __str__(self):
        return "Invitation for "+self.email+" in the organisation "+self.organisation.name+" with the role "+self.role


class UserResources(models.Model):
    """
    This class is used to define the fact that a user can like resources within the platform and he may
    wants to consult them regardless the fact he liked the resource doing an evaluation for an organization
    (!= Membership)
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resources = models.ManyToManyField("assessment.ExternalLink", blank=True)

    @classmethod
    def create_user_resources(cls, user):
        user_resources = cls(user=user)
        user_resources.save()

    def __str__(self):
        return self.user.email


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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
        list_pending_invitations = user.get_list_pending_invitation()
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

    def __str__(self):
        return str(self.user) + " in " + str(self.organisation) + " (" + self.role + ")"


class Organisation(models.Model):
    """

    """

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
        User,
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

    def get_pending_list(self):
        """
        This method returns the list of the pending invitations to join the organisation
        This is used to create rows for pending user invitations of the member array in orga-members.html
        :return: list of dictionaries
        """
        return list(PendingInvitation.objects.filter(organisation=self))


class ReleaseNote(models.Model):
    """
    Release Notes are used in the release-notes.html page by release_notes.py
    """
    date = models.DateField()
    text = models.TextField(null=False, blank=False)
    version = models.CharField(max_length=150)


def turn_list_orga_into_tuple(list_orga):
    """
    This function converts a list of organisations into a list of tuples (used gor the form to have choices)
    :param list_orga: list of organisations
    :return: list of tuples
    """
    list_tuple = []
    for orga in list_orga:
        list_tuple.append((orga.id, orga))
    return list_tuple


def get_list_all_staff_admin_platform():
    """
    This function returns the list of all the admin or staff users (an admin has necessarily the field 'staff'=True)
    :return: list of users
    """
    return list(User.object.filter(staff=True))
