from django.contrib.auth.forms import AuthenticationForm


def add_my_login_form(request):
    return {
        'login_form': AuthenticationForm(),
    }
