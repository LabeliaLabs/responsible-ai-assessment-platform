import json
import logging

from django.http import HttpResponse


logger = logging.getLogger('monitoring')


def export_user_data(request):
    """
    This function is used to export the user personal data.
    It uses the method get_all_data defined in the models file in User class
    """
    user = request.user
    jsonResponse = json.dumps(user.get_all_data())

    response = HttpResponse(jsonResponse)
    response["Content-Disposition"] = "attachment; filename=personal_data.json"
    logger.info(f"[data_export] The user {user.email} has exported his personal data")
    return response
