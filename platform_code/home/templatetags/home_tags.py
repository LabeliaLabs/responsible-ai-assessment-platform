from django import template
from django.utils.html import format_html
from home.models import Membership

register = template.Library()


@register.filter
def get_role(organisation, user):
    print("get role", organisation, user)
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
