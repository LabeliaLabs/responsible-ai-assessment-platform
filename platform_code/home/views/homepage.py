import logging

from django.http import HttpResponseRedirect
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    AuthenticationForm,
)
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views

from home.forms import PasswordResetForm_
from home.views.utils import manage_message_login_page

logger = logging.getLogger('monitoring')


def legal_notices_view(request):
    """ Render the legal notices page which has only static content. This page is accessible without login required"""
    return render(request, "home/legal-notices.html", {})


def faq_view(request):
    """ Render the FAQ page which has only static content. This page is accessible without login required"""
    return render(request, "home/faq.html", {})


class PasswordReset(auth_views.PasswordResetView):
    form_class = PasswordResetForm_  # Change the form because issue with is_active (and active in the User model)


class LogoutView(LogoutView):
    """ This CBV is used to logout the user and redirect to the homepage"""
    template_name = "home/logout.html"
    next_page = "home:homepage"  # View called when logout success


class LoginView(LoginView):
    """
    This CBV is used by the home page
    """

    form_class = AuthenticationForm
    template_name = "home/homepage.html"
    success_url = "home:user-profile"  # It s the view called when success, I define it here instead of in the settings

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
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
                    logger.info(f"[user_connection] The user {user.email} has logged in")
                    return HttpResponseRedirect(self.get_success_url())
                else:
                    return redirect("home:login")
            else:
                return redirect("home:login")


class LoginPageView(LoginView):
    """
    This class inherits from LoginView which manage the login popin.
    So all the logic is implemented over there, only the message displayed to the user is built here.
    """
    template_name = "home/login.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        # This will manage the message displayed to the user, whether is failed or he must login to access the content
        # or just to inform him that he needs to enter email & password, depending on his previous page
        message = manage_message_login_page(request)
        context["message"] = message
        return self.render_to_response(context)
