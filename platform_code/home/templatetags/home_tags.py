from django import template
from django.utils.safestring import mark_safe
from home.models import PlatformManagement

register = template.Library()


@register.filter
def get_role(organisation, user):
    """
    Get the role of the user membership in the organisation
    :param organisation: organisation
    :param user: user
    :return: string : "admin" or "read_only"
    """
    member = organisation.get_membership_user(user)
    if member:
        return member.role
    else:
        None


@register.filter
def eval_not_finished(query_evaluation):
    list_eval_not_finished = []
    for eval in query_evaluation:
        if not eval.is_finished:
            list_eval_not_finished.append(eval)
    return len(list_eval_not_finished)


@register.filter
def eval_finished(query_evaluation):
    list_eval_finished = []
    for eval in query_evaluation:
        if eval.is_finished:
            list_eval_finished.append(eval)
    return len(list_eval_finished)


@register.filter
def url_target_blank(text):
    """
    This function adds the target="_blank" attribute to <a></a> tag
    """
    return mark_safe(text.replace("<a ", '<a target="_blank" '))


@register.filter
def get_color(platform_management, color):
    """
    This function returns the main color of the platform
    """
    if not hasattr(platform_management, color):
        return ""
    return f"#{getattr(platform_management, color)}"


@register.filter
def get_platform_logo(platform_management):
    """
    This function returns the logo of the platform
    """
    return platform_management.logo