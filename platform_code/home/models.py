from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django_countries.fields import CountryField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin


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


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError(_('Users must have an email address'))

        user = self.model(
            email=self.normalize_email(email),

        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
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
    email = models.EmailField(
        verbose_name='email',
        max_length=255,
        unique=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    # TODO replace fields active, admin, staff by is_admin, is_active, is_staff and delete the modification in
    #  PasswordResetForm (in home/forms) and PasswordReset (in home/views)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)  # a admin user; non super-user
    admin = models.BooleanField(default=False)  # a superuser
    # notice the absence of a "Password field", that is built in.

    object = UserManager()
    USERNAME_FIELD = 'email'
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
        return {"email": self.email,
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
    """
    ADMIN = 'admin'
    READ_ONLY = "simple_user"

    ROLES = (
        (ADMIN, 'admin'),
        (READ_ONLY, "simple_user"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey("home.Organisation", blank=True, null=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=200, choices=ROLES, default=ADMIN)

    @classmethod
    def create_membership(cls, user, organisation, role):
        member = cls(user=user,
                     organisation=organisation,
                     role=role,
                     )
        member.save()

    def __str__(self):
        return str(self.user) + " in " + str(self.organisation) + " (" + self.role + ")"


class Organisation(models.Model):
    """

    """
    TEN = '0-9'
    FIFTY = '10-49'
    HUNDRED = '50-99'
    FIVEHUNDRED = '100-499'
    FIVETHOUSAND = '500-4999'
    PLUS = '>5000'

    SIZE = (
        (TEN, '0-9'),
        (FIFTY, '10-49'),
        (HUNDRED, '50-99'),
        (FIVEHUNDRED, '100-499'),
        (FIVETHOUSAND, '500-4999'),
        (PLUS, '>5000'),
    )

    # todo : if we keep this field, we need to work on translation
    AGRICULTURE = "Agriculture"
    AUDIO = "Audiovisuel / Spectacle"
    SOCIAL = "Social"
    ENERGIE = "Energie"
    CONSTRUCTION = "Construction aéronautique, ferroviaire et navale"
    PUBLIQUE = "Fonction publique"
    JOURNALISME = "Edition / Journalisme"
    RECHERCHE = "Recherche"
    ARMEE = "Armée / sécurité"
    SPORT = "Sport / Loisirs / Tourisme"
    EDUCTION = "Enseignement"
    CULTURE = "Culture / Artisanat d'art"
    HOTELLERIE = "Hôtellerie / Restauration"
    ART = "Art / Design"
    SANTE = "Santé"
    TRADUCTION = "Traduction / Interprétariat"
    AUTO = "Automobile"
    ENVIRONNEMENT = "Environnement"
    DROIT = "Droit / Justice"
    AGROALIMENTAIRE = 'Agroalimentaire'
    BANQUE = "Banque / Assurance"
    BOIS = "Bois / Papier / Carton / Imprimerie"
    BTP = "BTP / Architecture / Matériaux de construction"
    CHIMIE = "Chimie / Parachimie"
    COMMERCE = "Commerce / Négoce / Distribution"
    COM = "Marketing / Communication / Multimédia"
    ELECTRONIQUE = "Électronique / Électricité"
    CONSEIL = "Gestion / Conseil / Audit"
    PHARMA = "Industrie pharmaceutique"
    INFORMATIQUE = "Informatique / Télécoms"
    MACHINE = "Machines et équipements / Mécanique"
    METALLURGIE = "Métallurgie / Travail du métal"
    PLASTIQUE = "Plastique / Caoutchouc"
    TEXTILE = "Textile / Habillement / Chaussure"
    TRANSPORT = "Transports / Logistique"
    AUTRE = "Autre"

    SECTOR = (

        (AGRICULTURE, "Agriculture"),
        (AGROALIMENTAIRE, 'Industrie Agroalimentaire'),
        (ARMEE, "Armée / sécurité"),
        (ART, "Art / Design"),
        (AUDIO, "Audiovisuel / Spectacle"),
        (AUTO, "Automobile"),
        (BANQUE, "Banque / Assurance"),
        (BOIS, "Bois / Papier / Carton / Imprimerie"),
        (BTP, "BTP / Architecture / Matériaux de construction"),
        (CHIMIE, "Chimie / Parachimie"),
        (COMMERCE, "Commerce / Négoce / Distribution"),
        (COM, "Communication / Marketing / Multimédia"),
        (CONSTRUCTION, "Construction aéronautique, ferroviaire et navale"),
        (CULTURE, "Culture / Artisanat d'art"),
        (DROIT, "Droit / Justice"),
        (ELECTRONIQUE, "Électronique / Électricité"),
        (ENERGIE, "Energie"),
        (EDUCTION, "Enseignement"),
        (ENVIRONNEMENT, "Environnement"),
        (PUBLIQUE, "Fonction publique"),
        (CONSEIL, "Gestion / Conseil / Audit"),
        (HOTELLERIE, "Hôtellerie / Restauration"),
        (PHARMA, "Industrie pharmaceutique"),
        (INFORMATIQUE, "Informatique / Télécoms"),
        (JOURNALISME, "Journalisme / Edition"),
        (MACHINE, "Machines et équipements / Mécanique"),
        (METALLURGIE, "Métallurgie / Travail du métal"),
        (PLASTIQUE, "Plastique / Caoutchouc"),
        (RECHERCHE, "Recherche"),
        (SANTE, "Santé"),
        (SOCIAL, "Social"),
        (SPORT, "Sport / Loisirs / Tourisme"),
        (TEXTILE, "Textile / Habillement / Chaussure"),
        (TRADUCTION, "Traduction / Interprétariat"),
        (TRANSPORT, "Transports / Logistique"),
        (AUTRE, "Autre"),

    )

    name = models.CharField(max_length=200)
    size = models.CharField(max_length=200, choices=SIZE)
    created_by = models.ForeignKey(User, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="created_by")
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
        organisation = cls(name=name, size=size, country=country, sector=sector, created_by=created_by)
        organisation.save()
        Membership.create_membership(user=created_by, role="admin", organisation=organisation)
        return organisation

    def __str__(self):
        return self.name

    def get_list_members(self):
        """
        Get the list of the members of the organisation
        :return: list
        """
        return list(Membership.objects.filter(organisation=self))

    def count_members(self):
        return str(len(self.get_list_members()))

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
        except Membership.DoesNotExist:
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


def get_list_organisations_where_user_is_admin(user):
    """
    This function is used to obtain the list of organisations the user is member as admin
    :param user: user
    :return: list of organisations
    """
    print("get_list_organisations_where_user_is_admin", list(Organisation.objects.distinct().filter(membership__user=user, membership__role="admin")))
    return list(Organisation.objects.distinct().filter(membership__user=user, membership__role="admin"))


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
