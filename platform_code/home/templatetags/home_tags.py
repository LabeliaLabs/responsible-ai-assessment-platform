from django import template
from home.models import Membership

register = template.Library()


@register.filter
def get_role(organisation, user):
    """
    Get the role of the user membership in the organisation
    :param organisation: organisation
    :param user: user
    :return: string : "admin" or "read_only"
    """
    member = Membership.objects.get(user=user, organisation=organisation)
    return member.role


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
