import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import generic
from django.contrib.auth.views import (
    PasswordChangeForm,
    update_session_auth_hash,
    )
from django.utils.translation import gettext as _

from home.forms import DataSettingsForm
from home.models import User


logger = logging.getLogger('monitoring')


class ProfileSettingsView(LoginRequiredMixin, generic.DetailView):
    template_name = "home/profile-settings.html"
    model = User
    login_url = "home:login"
    redirect_field_name = "home:homepage"
    data_update = {}

    def get(self, request, *args, **kwargs):

        user = request.user
        self.object = user
        context = self.get_context_data(object=self.object)
        context["user_data_form"] = DataSettingsForm(user=user)

        context["change_password_form"] = PasswordChangeForm(user=user)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            dic_form = request.POST.dict()

            data_update = {"success": False, "error_messages": []}
            # It means the user change his password
            if "old_password" in dic_form:
                self.treat_password_change(request)

            elif "last_name" in dic_form:
                self.treat_name_change(request)

            return HttpResponse(json.dumps(data_update), content_type="application/json")

    def treat_password_change(self, request):
        """
        Treat the POST case where the user wants to change his passwords.
        Updates the data_update dictionary.
        """
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            self.data_update["success"] = True
            logger.info(f"[password_changed] The user {user.email} has changed his password.")
            self.data_update["message_success"] = _("Your password has been changed!")
        else:
            all_error_data = json.loads(form.errors.as_json())  # need dict format to extract error code
            error_list_values = list(all_error_data.values())[0]

            for error_dic in error_list_values:
                self.data_update["error_messages"].append(error_dic.get("message"))

    def treat_name_change(self, request):
        """
        Treat the POST case where the user wants to change his name.
        Updates the data_update dictionary.
        """
        user = request.user
        form = DataSettingsForm(request.POST, user=user)
        if form.is_valid():
            last_name = form.cleaned_data.get("last_name")
            first_name = form.cleaned_data.get("first_name")
            user.last_name = last_name
            user.first_name = first_name
            user.save()
            self.data_update["success"] = True
            self.data_update["message_success"] = _("Your personal data have been updated!")
        else:
            self.data_update["message_fail"] = _("The validation failed. Please check you have filled all the fields.")