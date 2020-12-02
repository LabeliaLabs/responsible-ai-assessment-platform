import logging

from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import render


logger = logging.getLogger('monitoring')

VIEW_ERRORS = {
    404: {
        "title": _("404 - Page not found"),
        "content": _("Sorry, the page has not been found or does not exist !"),
    },
    500: {"title": _("Internal error"), "content": _("An internal error occured"), },
    403: {
        "title": _("Permission denied"),
        "content": _("Sorry, you can not access this content"),
    },
    400: {"title": _("Bad request"), "content": _("There is an error in the request"), },
}


def error_view_handler(request, exception, status):
    return render(
        request,
        template_name="errors.html",
        status=status,
        context={
            "error": exception,
            "status": status,
            "title": VIEW_ERRORS[status]["title"],
            "content": VIEW_ERRORS[status]["content"],
        },
    )


def error_404_view_handler(request, exception=None):
    logger.error(f"[error_404] Error 404 for the request {request}, exception {exception}")
    return error_view_handler(request, exception, 404)


def error_500_view_handler(request, exception=None):
    logger.error(f"[error_500] Error 500 for the request {request}, exception {exception}")
    return error_view_handler(request, exception, 500)


def error_403_view_handler(request, exception=None):
    messages.warning(request, _("You don't have access to this content."))
    logger.error(f"[error_403] Error 403 for the request {request}, exception {exception}")
    return HttpResponseRedirect("/home/")
    # return redirect("home:homepage")
    # return error_view_handler(request, exception, 403)


def error_400_view_handler(request, exception=None):
    logger.error(f"[error_400] Error 400 for the request {request}, exception {exception}")
    return error_view_handler(request, exception, 400)
