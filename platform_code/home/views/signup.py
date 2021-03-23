import logging
from datetime import datetime, timedelta
import jwt

from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.utils.translation import gettext as _, ngettext, get_language
from django.conf import settings

from home.forms import SignUpForm
from home.models import User, UserResources, Membership


logger = logging.getLogger('monitoring')


def signup(request):
    """
    This function is used when the user wants to sign up, ie he wants to create a new account
    It is call from the login pop-in, with the "sign-up button"
    If success, save the user and login, create UserResources (to manage the resources the user likes)
    :param request:
    :return:
    """
    if request.method == "POST":
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
                'token': jwt.encode({"user": user.email,
                                     "exp": datetime.now()+timedelta(days=5)},  # You can edit the delay token validity
                                    settings.SECRET_KEY, algorithm='HS256').decode("utf-8"),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            logger.info(f"[account_creation] The user {user.email} created an account")
            return render(request, "home/account/acc_activate_done.html")
    else:
        form = SignUpForm()
    return render(request, "home/signup.html", {"form": form})


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
    except jwt.ExpiredSignatureError as e:
        messages.error(request, _("The link has expired."))
        logger.error(f"[account_activation_error] The token of an account validation has expired, "
                     f"uid {uidb64}, error {e}")
    if user is not None and token_decoded == user.email:
        user.active = True
        user.save()
        login(request, user)
        # If the user has pending invitations
        if user.get_list_pending_invitation():
            list_pending_invitation = user.get_list_pending_invitation()
            count = len(list_pending_invitation)
            list_organisations = [x.organisation.name for x in list_pending_invitation]
            name = str(list_organisations).replace('[', '').replace(']', '').replace('\'', '')
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
