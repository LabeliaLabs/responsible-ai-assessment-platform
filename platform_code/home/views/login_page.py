import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate

from home.forms import RegisterForm
from .utils import manage_message_login_page


logger = logging.getLogger('monitoring')


def login_view(request):
    """
    Login function when user is redirected to the login.
    :param request:
    :return:
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        email = request.POST["username"]  # Which is actually the email
        password = request.POST["password"]
        user = authenticate(email=email, password=password)
        if user is not None and user.active:
            login(request, user)
            logger.info(f"[user_connection] The user {user.email} has logged in")
            return redirect("home:user-profile")
        else:
            message = manage_message_login_page(request)
    else:
        form = RegisterForm()
        message = manage_message_login_page(request)
    return render(request, "home/login.html", {"form": form, "message": message})
