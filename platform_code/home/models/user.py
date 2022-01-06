from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


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
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    language_preference = models.CharField(default="fr", choices=languages, max_length=15)
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
