from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import activate

from home.models import PlatformManagement


def add_my_login_form(request):
    return {
        'login_form': AuthenticationForm(auto_id=False),
    }


def add_platform_management(request):
    platform_management = PlatformManagement.get_or_create()
    # If the languages are not activated (English), the site is in French
    if not platform_management.activate_multi_languages:
        activate("fr")
    return {
        'platform_management': platform_management
    }
