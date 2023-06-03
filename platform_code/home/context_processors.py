from assessment.models import is_language_activation_allowed
from django.utils.translation import activate
from home.models import Footer, PlatformManagement


def add_footer_list(request):
    return {
        "footer_list": Footer.objects.all(),
    }


def add_platform_management(request):
    if PlatformManagement.objects.all().count() > 1:
        while PlatformManagement.objects.all().count() > 1:
            PlatformManagement.objects.last().delete()
        platform_management = PlatformManagement.objects.first()
    else:
        platform_management = PlatformManagement.get_or_create()
    # If the languages are not activated (English), the site is in French
    if not platform_management.activate_multi_languages:
        activate("fr")
    return {
        "platform_management": platform_management,
        "is_language_activation_allowed": is_language_activation_allowed(),
    }
