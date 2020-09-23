from django import forms
from django.contrib.auth.forms import UserCreationForm, _unicode_ci_compare
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import User, Organisation

UserModel = get_user_model()


class SignUpForm(UserCreationForm):
    # username = forms.CharField(required=False) # Username not used as it is replaced by email
    email = forms.EmailField(max_length=254)
    first_name = forms.CharField(
        max_length=30, required=True, label=_("First_name")
    )
    last_name = forms.CharField(
        max_length=30, required=True, label=_("Last_name")
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=_(
            "Your password must contain at least 8 characters, with at least one number and one letter"
        ),
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class OrganisationCreationForm(ModelForm):
    """
    This form is used when the user wants to create an organisation
    There are 2 possible ways: user in his profile view wants to start an eval but the user has not orga associated with
    his account so a special url to display this form; the user in his profile view wants to create an organisation
    so a pop-in appears with this form (see how it renders with pop-in)
    """

    class Meta:
        model = Organisation
        exclude = ("created_by",)

    def __init__(self, *args, **kwargs):
        super(OrganisationCreationForm, self).__init__(*args, **kwargs)
        self.fields["country"].initial = "FR"


class DataSettingsForm(ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label=_("First_name"))
    last_name = forms.CharField(max_length=30, required=True, label=_("Last_name"))

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(DataSettingsForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["first_name"].label = _("First_name")
        #self.fields["last_name"].label = _("Last_name")  # todo do not work currently, I DON T KNOW WHY .....
        self.fields["last_name"].label = "Nom"



# USER PART #


from django.contrib.auth.forms import ReadOnlyPasswordHashField, PasswordResetForm


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError(_("email is taken"))
        return email

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2


class UserAdminCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes all the required
    fields, plus a repeated password.
    """

    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"), widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class PasswordResetForm_(PasswordResetForm):
    """
    Just override the get_user method and change the user.is_active to user.active
    """

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        email_field_name = UserModel.get_email_field_name()
        active_users = UserModel._default_manager.filter(
            **{"%s__iexact" % email_field_name: email, "active": True, }
        )
        return (
            u
            for u in active_users
            if u.has_usable_password()
            and _unicode_ci_compare(email, getattr(u, email_field_name))
        )