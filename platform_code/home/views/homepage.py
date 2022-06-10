import logging
from datetime import datetime, timedelta
import jwt
from sentry_sdk import set_user

from django.http import HttpResponseRedirect
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext as _, ngettext, get_language
from django.conf import settings

from home.forms import PasswordResetForm_, SignUpForm
from assessment.templatetags.assessment_tags import stringify_list
from home.models import User, UserResources, Membership, PendingInvitation


logger = logging.getLogger('monitoring')


class PasswordReset(auth_views.PasswordResetView):
    form_class = PasswordResetForm_  # Change the form because issue with is_active (and active in the User model)


class LogoutView(LogoutView):
    """ This CBV is used to logout the user and redirect to the homepage"""
    template_name = "home/logout.html"
    next_page = "home:homepage"  # View called when logout success


class HomepageView(LoginView):
    """
    This CBV is used by the home page
    """

    form_class = AuthenticationForm
    template_name = "home/homepage.html"
    success_url = "home:user-profile"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["login_form"] = AuthenticationForm()
        context["signup_form"] = SignUpForm()
        return context

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            if request.POST["action"] == "login":
                return self.login(request, args, kwargs)
            elif request.POST['action'] == 'signup':
                return self.signup(request, args, kwargs)
            else:
                return redirect("home:homepage")

    def login(self, request, *args, **kwargs):
        # Redirect to user profile if he is already logged
        if request.user.is_authenticated:
            return redirect("home:user-profile")

        form = self.form_class(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            # Ensure the user-originating redirection url is safe.
            user = authenticate(email=email, password=password)
            if user is not None and user.active:
                login(self.request, user)
                set_user({"email": email})
                logger.info(f"[user_connection] The user {user.email} has logged in")
                return HttpResponseRedirect(self.get_success_url())
            else:
                return redirect("home:homepage")
        else:
            context = self.get_context_data()
            context["message_login"] = {
                "alert-warning":
                    _("The attempt to connect with this combination email/password failed. Please try again!")
            }
            return self.render_to_response(context)

    def signup(self, request, *args, **kwargs):
        """
        This function is used when the user wants to sign up, ie he wants to create a new account
        It is call from the login pop-in, with the "sign-up button"
        If success, save the user and login, create UserResources (to manage the resources the user likes)
        :param request:
        :return:
        """
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get("email")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(email=email, password=raw_password)
            user.language_preference = get_language()
            user.active = False
            user.save()
            # create user_resources so the user can access resources, this could be integrated to user creation ?
            UserResources.create_user_resources(user=user)
            current_site = get_current_site(request)
            # Activez votre compte Assessment Data science responsable et de confiance
            mail_subject = _("Activate your trustworthy Data Science Assessment account")
            message = render_to_string('home/account/acc_activate_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': "http" if settings.DEBUG else "https",
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': jwt.encode(
                    {"user": user.email, "exp": datetime.now() + timedelta(days=5)},
                    settings.SECRET_KEY,
                    algorithm='HS256'
                ).decode("utf-8"),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            logger.info(f"[account_creation] The user {user.email} created an account")
            return render(request, "home/account/acc_activate_done.html")
        context = self.get_context_data()
        context["signup_form"] = form
        return render(request, "home/homepage.html", context)


def activate(request, uidb64, token):
    # Activate the account
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.object.get(pk=uid)
    except(TypeError, ValueError, OverflowError, ObjectDoesNotExist) as e:
        user = None
        # Todo find better log item to display
        logger.error(f"[account_activation_error] The user with uidb64 {uidb64} does not exist, error {e}.")
    try:
        token_decoded = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')["user"]
    except (KeyError, NameError, jwt.InvalidSignatureError, jwt.InvalidAlgorithmError, jwt.InvalidTokenError) as e:
        token_decoded = None
        logger.error(f"[account_activation_error] There is an issue to decode the token for the request {request},"
                     f" with uid {uidb64}, error {e}")
    if user is not None and token_decoded == user.email:
        user.active = True
        user.save()
        login(request, user)
        # If the user has pending invitations
        if PendingInvitation.get_list_pending_invitation(user):
            list_pending_invitation = PendingInvitation.get_list_pending_invitation(user)
            count = len(list_pending_invitation)
            list_organisations = [x.organisation.name for x in list_pending_invitation]
            name = stringify_list(list_organisations)
            Membership.create_membership_pending_invitations(user=user)
            logger.info(f"[account_creation][join_organisation] The user {user.email} created an account and has "
                        f"joined the organisations where he was invited, {list_pending_invitation}")
            messages.success(request, ngettext("Thank you for your verification, your account has been activated."
                                               "You had %(count)d pending "
                                               "invitation to join the organisation: %(name)s. "
                                               "You have automatically joined it.",
                                               "Thank you for your verification, your account has been activated."
                                               "You had %(count)d pending "
                                               "invitations to join the organisations: %(name)s. "
                                               "You have automatically joined them.",
                                               count
                                               ) % {
                                 'count': count,
                                 'name': name
                             }
                             )
            return redirect("home:user-profile")
        else:
            # The user is redirected to orga-creation but can skip this action
            logger.info(f"[account_activated] The user {user.email} activated his account")
            messages.success(request, _("Your account has been activated! \n Do you want to create your organisation"
                                        " now? "
                                        "You could do it later but it is required to do an evaluation."))

            return redirect("home:orga-creation")

    else:
        messages.error(request, _("An issue occurred with the link."))
        logger.error(f"[account_activation_error] The activation of the account failed, request {request}"
                     f", uidb64 {uidb64}")
        return redirect("home:homepage")
