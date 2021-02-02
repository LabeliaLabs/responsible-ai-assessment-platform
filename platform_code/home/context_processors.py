from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import activate

from home.models import PlatformManagement
from assessment.models import is_language_activation_allowed


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
        'platform_management': platform_management,
        'is_language_activation_allowed': is_language_activation_allowed()
    }
