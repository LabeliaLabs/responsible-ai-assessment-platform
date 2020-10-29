# IMPORTS #

import json
import logging
from datetime import datetime, timedelta

import jwt

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic
from django.contrib.auth.views import (
    login_required, LoginView, LogoutView, PasswordChangeForm, AuthenticationForm, auth_login,
    FormView, update_session_auth_hash,
    )
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views
from django.utils.translation import gettext as _
from django.conf import settings

from assessment.views import treat_resources, error_500_view_handler, error_400_view_handler
from assessment.forms import EvaluationMutliOrgaForm, EvaluationForm
from assessment.models import Assessment, Evaluation, get_last_assessment_created
from .forms import SignUpForm, OrganisationCreationForm, RegisterForm, DataSettingsForm, PasswordResetForm_
from .models import User, UserResources, Organisation, Membership

logger = logging.getLogger('monitoring')

# Functions #


def signup(request):
    """
    This function is used when the user wants to sign up, ie he wants to create a new account
    It is call from the login pop-in, with the "sign-up button"
    If success, save the user and login, create UserResources (to manage the resources the user likes)
    :param request:
    :return:
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get("email")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(email=email, password=raw_password)
            user.active = False
            user.save()
            # create user_resources so the user can access resources, this could be integrated to user creation ?
            UserResources.create_user_resources(user=user)
            current_site = get_current_site(request)
            mail_subject = _("Activate your Substra account.")
            message = render_to_string('home/account/acc_activate_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': "https" if request.is_secure() else "http",
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': jwt.encode({"user": user.email,
                                     "exp": datetime.now()+timedelta(days=5)},  # You can edit the delay token validity
                                    settings.SECRET_KEY, algorithm='HS256').decode("utf-8"),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            logger.info(f"[account_creation] The user {email} created an account")
            return render(request, "home/account/acc_activate_done.html")
    else:
        form = SignUpForm()
    return render(request, "home/signup.html", {"form": form})


def activate(request, uidb64, token):
    # Activate the account
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.object.get(pk=uid)
    except(TypeError, ValueError, OverflowError, ObjectDoesNotExist) as e:
        user = None
        # Todo find better log item to display
        logger.error(f"[account_activation_error] The user with uidb64 {uidb64} does not exist, error {e}.")
    try:
        token_decoded = jwt.decode(token, settings.SECRET_KEY, algorithm='HS256')["user"]
    except (KeyError, NameError, jwt.InvalidSignatureError, jwt.InvalidAlgorithmError, jwt.InvalidTokenError) as e:
        token_decoded = None
        logger.error(f"[account_activation_error] There is an issue to decode the token for the request {request},"
                     f" with uid {uidb64}, error {e}")
    except jwt.ExpiredSignatureError as e:
        messages.error(request, _("The link has expired."))
        logger.error(f"[account_activation_error] The token of an account validation has expired, "
                     f"uid {uidb64}, error {e}")
    if user is not None and token_decoded == user.email:
        user.active = True
        user.save()
        login(request, user)
        # return redirect('home')
        messages.success(request, _("Thank you for the verification, your account has been activated!"))
        logger.info(f"[account_activated] The user {user.email} activated his account")
        return redirect("home:user-profile")
    else:
        messages.error(request, _("An issue occured with the link."))
        logger.error(f"[account_activation_error] The activation of the account failed, request {request}"
                     f", uidb64 {uidb64}")
        return redirect("home:homepage")


@login_required(login_url="/login/")
def delete_user(request):
    """
    When the user wants to delete his account. First he needs to be login.
    If it s ok, we need to delete his memberships, his userresources, and the case where his is the only admin of
    an orga, the orga. As the evaluations of the orga are "models.CASCADE", the evaluations will be deleted
    automatically.
    If the user is not the only admin of the orga, we won't delete it, and we won't delete the evaluation he has
    created also because they may be useful for the other admins.

    :param request:
    :return:
    """

    user = request.user
    list_orga_user_is_admin = user.get_list_organisations_where_user_as_role(role="admin")
    for orga in list_orga_user_is_admin:
        # If the user is the only admin of the organisation
        if orga.count_admin_members() == 1:
            # Delete the organisation and thus, the evaluations attached (CASCADE)
            logger.info(f"[organisation_deletion] The orga {orga.name} has been deleted with the deletion of "
                        f"the user account {user.email}")
            orga.delete()
    # UserResources is deleted on CASCADE
    # Membership is deleted on CASCADE
    logger.info(f"[account_deletion] The user {user.email} has deleted his account")
    user.delete()
    # Todo use django.utils.translation.ngettext for the plurial
    if len(list_orga_user_is_admin) == 0:
        messages.success(request, _("Your account has been deleted"))
    elif len(list_orga_user_is_admin) == 1:
        messages.success(request, _(f"Your account has been deleted as well as"
                                    f" the organisation {list_orga_user_is_admin[0]} and its evaluations."))
    else:
        messages.success(
            request,
            _(f"Your account has been deleted as well as the organisations:"
              f" {str(list_orga_user_is_admin).replace('[', '').replace(']', '')} and their linked evaluations."),
        )
    return redirect("home:homepage")


def login_view(request):
    """
    Login function when user is redirected to the login.
    :param request:
    :return:
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        email = request.POST["username"]  # Which is actually the email
        password = request.POST["password"]
        user = authenticate(email=email, password=password)
        if user is not None and user.active:
            login(request, user)
            logger.info(f"[user_connection] The user {user.email} has logged in")
            return redirect("home:user-profile")
        else:
            message = manage_message_login_page(request)
    else:
        form = RegisterForm()
        message = manage_message_login_page(request)
    # TODO add message if redirect "vous devez vous connecter", if redirect from signup "connexion",
    #  if user fail " alert-danger : bad username or pwd"
    return render(request, "home/login.html", {"form": form, "message": message})


def export_user_data(request):
    """ This function is used to export the user personal data.
     It uses the method get_all_data defined in the models file in User class"""
    user = request.user
    jsonResponse = json.dumps(user.get_all_data())

    response = HttpResponse(jsonResponse)
    response["Content-Disposition"] = "attachment; filename=personal_data.json"
    logger.info(f"[data_export] The user {user.email} has exported his personal data")
    return response


def about_view(request):
    """ Render the about page which has only static content. This page is accessible without login required"""
    return render(request, "home/about.html", {})


def legal_notices_view(request):
    """ Render the legal notices page which has only static content. This page is accessible without login required"""
    return render(request, "home/legal-notices.html", {})

# CBV #


class LoginView(LoginView):
    """
    This CBV is used by the home page
    """

    form_class = AuthenticationForm
    template_name = "home/homepage.html"
    success_url = "home:user-profile"  # It s the view called when success, I define it here instead of in the settings

    def form_valid(self, form):
        """
        If the login is valid, redirect to the user profile
        :param form:
        :return:
        """
        """Security check complete. Log the user in."""
        auth_login(self.request, form.get_user())
        return redirect("home:user-profile")

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            # Redirect to user profile if he is already logged
            if request.user.is_authenticated:
                return redirect("home:user-profile")

            form = self.form_class(data=request.POST)
            if form.is_valid():
                # TODO check if there is not a better way (change in the forms)
                email = form.cleaned_data.get(
                    "username"
                )  # Switch the function, actually email
                password = form.cleaned_data.get("password")
                # Ensure the user-originating redirection url is safe.
                user = authenticate(email=email, password=password)
                if user is not None and user.active:
                    login(self.request, user)
                    logger.info(f"[user_connection] The user {user.email} has logged in")
                    return HttpResponseRedirect(self.get_success_url())
                else:
                    return redirect("home:login")
            else:
                return redirect("home:login")


class LogoutView(LogoutView):
    """ This CBV is used to logout the user and redirect to the homepage"""
    template_name = "home/logout.html"
    next_page = "home:homepage"  # View called when logout success


class ResourcesView(LoginRequiredMixin, generic.DetailView):
    """ This CBV is used to define the content of the resource page, accessible from the nav bar.
     This page is different from the resource page of the user dashboard although the template is almost the same"""
    model = User
    template_name = 'home/resources.html'
    login_url = 'home:login'
    redirect_field_name = 'home:homepage'

    def get(self, request, *args, **kwargs):
        user = request.user
        self.object = user
        context = self.get_context_data(object=user)

        # Catch the userresources object
        if len(UserResources.objects.filter(user=user)) == 1:
            user_resources = UserResources.objects.get(user=user)
        # Case the user resource does not exist, which should not happen
        # but it does when you create super user with the shell
        elif len(UserResources.objects.filter(user=user)) == 0:
            UserResources.create_user_resources(user=user)  # create user_resources so the user can access resources
            user_resources = UserResources.objects.get(user=user)
        else:
            logger.error(f"[multiple_user_resources] The user {user.email} has multiple user resources")
            error_500_view_handler(request, exception=MultipleObjectsReturned())

        query_resources_dict = user_resources.resources.all()
        context["resources"] = query_resources_dict
        context["resources_liked"] = request.user.userresources.resources.all()

        if get_last_assessment_created():
            context['last_version'] = get_last_assessment_created().version  # get last version
        else:
            context['last_version'] = None
        context["last_assessment"] = get_last_assessment_created()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            if "resource_id" in request.POST.dict():
                # The function is defined in assessment/views and add or remove the resource to the user_resource m2m
                # field 'resources'
                return treat_resources(request)


class ProfileView(LoginRequiredMixin, generic.DetailView):
    model = User
    template_name = "home/profile.html"
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):

        user = request.user
        self.object = user
        context = self.get_context_data(object=user)
        # Catch the userresources object
        if len(UserResources.objects.filter(user=user)) == 1:
            user_resources = UserResources.objects.get(user=user)
        # Case the user resource does not exist, which should not happen
        # but it does when you create super user with the shell
        elif len(UserResources.objects.filter(user=user)) == 0:
            UserResources.create_user_resources(user=user)  # create user_resources so the user can access resources
            user_resources = UserResources.objects.get(user=user)
        else:
            logger.error(f"[multiple_user_resources] The user {user.email} has multiple user resources")
            error_500_view_handler(request, exception=MultipleObjectsReturned())

        # not the resources but the dictionary of resources' info
        query_resources_dict = user_resources.resources.all()

        context["resources"] = query_resources_dict
        context["resources_liked"] = request.user.userresources.resources.all()

        # Get the organisations where the user is member to
        organisation_list = []
        # Can be empty query
        query_membership = Membership.objects.filter(
            user=user
        )  # Possibility to add a condition on the role

        for membership in query_membership:
            organisation_list.append(membership.organisation)
        context["organisations"] = organisation_list
        # Get the evaluations created by the user
        # This can be modified if we want all the evaluations of the organisations the user belong to
        # Can be empty
        # Todo tests
        list_evaluations = Evaluation.objects.filter(organisation__membership__user=user,
                                                     organisation__membership__role="admin").order_by("-created_at")
        context["evaluations"] = list_evaluations
        context["evaluation_form_dic"] = {}
        for evaluation in list_evaluations:
            context["evaluation_form_dic"][str(evaluation.id)] = EvaluationForm(name=evaluation.name)
        context["new_orga_form"] = OrganisationCreationForm()
        context["new_evaluation_form"] = EvaluationMutliOrgaForm(user=user)

        if get_last_assessment_created():
            context[
                "last_version"
            ] = get_last_assessment_created().version  # get last version
            context["last_assessment"] = get_last_assessment_created()
        else:
            context["last_version"] = []
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Manage the different forms there are in this view (organisation creation and evaluation creation).
        The way this is manage can be improved but currently it is working. We check if there are key words of
        each form in the request.POST dictionary
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if request.method == 'POST':

            user = request.user
            # Differentiate between the organisation creation and the evaluation creation
            # It could be done with the form id but easier this way, may be to improve
            # If the sector is in the form, it means it is the organisation creation form, else evaluation creation
            if "sector" in request.POST:
                # create a form instance and populate it with data from the request:
                form = OrganisationCreationForm(request.POST)
                # check whether it's valid:
                if form.is_valid():
                    user = user
                    name = form.cleaned_data.get("name")
                    size = form.cleaned_data.get("size")
                    country = form.cleaned_data.get("country")
                    sector = form.cleaned_data.get("sector")
                    organisation = Organisation.create_organisation(
                        name=name,
                        size=size,
                        country=country,
                        sector=sector,
                        created_by=user,
                    )
                    logger.info(f"[organisation_creation] A new organisation {organisation.name} has been "
                                f"created by the user {user.email}")
                    # redirect to a new URL:
                    response = redirect("assessment:orga-summary", organisation.id)
                    return response
                else:
                    return self.form_invalid(form)

            # If there is "organisation" in the form, it is a Evaluation creation form
            elif "organisation" in request.POST:

                # If the user belongs to multiple organisation, it is a form with a field organisation
                if len(user.get_list_organisations_where_user_as_role(role="admin")) >= 1:
                    form = EvaluationMutliOrgaForm(
                        request.POST,
                        user=user,
                        # organisation=request.POST.get("organisation"),
                    )
                    # organisation = request.POST.get('organisation')
                    # form.fields['organisation'].choices = [(organisation, organisation)]

                    if form.is_valid():
                        name = form.cleaned_data.get("name")
                        organisation = form.cleaned_data.get("organisation")
                        last_version_in_organisation = organisation.get_last_assessment_version()
                        eval = Evaluation.create_evaluation(
                            name=name,
                            assessment=get_last_assessment_created(),
                            organisation=organisation,
                            user=user,
                        )
                        eval.create_evaluation_body()
                        logger.info(f"[evaluation_creation] The user {user.email} has created an evaluation "
                                    f"{eval.name} for the organisation {organisation}")
                        if last_version_in_organisation and \
                                last_version_in_organisation < float(get_last_assessment_created().version):
                            # print("fetch eval", eval)
                            origin_assessment = get_object_or_404(Assessment, version=str(last_version_in_organisation))
                            eval.fetch_the_evaluation(origin_assessment=origin_assessment)
                        # redirect to a new URL:
                        response = redirect(
                            "assessment:evaluation",
                            organisation.id,
                            eval.slug,
                            eval.pk,
                        )
                        return response
                    else:
                        # TODO treat invalid form
                        return redirect("home:orga-creation")

                # Case the user doesn't belong to an organisation as admin, he shouldn t be able to create an evaluation
                # So we redirect to organisation creation
                else:
                    return redirect("home:orga-creation")

            # If resource id in the post, the user unliked a resource from his resource liked page
            # Or if the ajax if when the user likes/unlikes a resource
            elif "resource_id" in request.POST.dict():
                # The function is defined in assessment/views and add or remove the resource to the user_resource m2m
                # field 'resources'
                return treat_resources(request)

            # If the user edits the name of the evaluation
            elif "name" in request.POST.dict():
                data_update = {"success": False, "message": _("An error occurred")}
                form = EvaluationForm(request.POST)
                if form.is_valid():
                    name = form.cleaned_data.get("name")
                    evaluation_id = int(request.POST.dict().get("evaluation_id"))
                    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
                    evaluation.name = name
                    evaluation.save()
                    data_update["success"] = True
                    data_update["message"] = _("The evaluation's name has been changed")
                    logger.info(f"[evaluation_name_changed] The user {request.user.email} changed the named of the "
                                f"evaluation (id: {evaluation_id})")
                return HttpResponse(json.dumps(data_update), content_type="application/json")

            # Case there is a post which is not managed by the function
            else:
                logger.error("[post_error] The post in ProfilView is not managed by any case.")
                error_400_view_handler(request)


class ProfileSettingsView(LoginRequiredMixin, generic.DetailView):
    template_name = "home/profile-settings.html"
    model = User
    login_url = "home:login"
    redirect_field_name = "home:homepage"

    def get(self, request, *args, **kwargs):
        print(request.user)
        user = request.user
        self.object = user
        context = self.get_context_data(object=self.object)
        context["user_data_form"] = DataSettingsForm(user=user)

        context["change_password_form"] = PasswordChangeForm(user=user)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            dic_form = request.POST.dict()
            user = request.user
            data_update = {"success": False, "error_messages": []}
            # It means the user change his password
            if "old_password" in dic_form:
                form = PasswordChangeForm(request.user, request.POST)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important!
                    data_update["success"] = True
                    logger.info(f"[password_changed] The user {user.email} has changed his password.")
                    # todo solve bug translation
                    # data_update["message_success"] = _("Your password has been changed!")
                    data_update["message_success"] = "Votre mot de passe a bien été changé !"
                else:
                    all_error_data = json.loads(
                        form.errors.as_json()
                    )  # need dict format to extract error code
                    error_list_values = list(all_error_data.values())[0]

                    for error_dic in error_list_values:
                        data_update["error_messages"].append(error_dic.get("message"))

            elif "last_name" in dic_form:
                form = DataSettingsForm(request.POST, user=user)
                if form.is_valid():
                    last_name = form.cleaned_data.get("last_name")
                    first_name = form.cleaned_data.get("first_name")
                    user.last_name = last_name
                    user.first_name = first_name
                    user.save()
                    data_update["success"] = True
                    # todo : solve bug translation
                    # data_update["message_success"] = _("Your personnal data have well been updated!")
                    data_update["message_success"] = "Vos données personnelles ont bien été mises à jour."
                else:
                    # data_update["message_fail"] = _("The validation failed. Please check you have well filled all the"
                    #                                "fields")
                    data_update["message_fail"] = "La validation a échouée. Vérifiez que vous avez bien rempli" \
                                                  " tous les champs."

            return HttpResponse(
                json.dumps(data_update), content_type="application/json"
            )


class OrganisationCreationView(LoginRequiredMixin, FormView):
    """
    When the user wants to create an evaluation where as he hasn't an organisation, we need to create the organisation
    """

    template_name = "home/profile-organisation-creation.html"
    model = Organisation
    login_url = "home:login"
    redirect_field_name = "home:homepage"
    form_class = OrganisationCreationForm
    success_url = "assessment:creation-evaluation"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        previous_url = request.META.get("HTTP_REFERER")

        if (
            previous_url is not None and "signup" in previous_url
        ):  # TODO check if it is logic (refresh page)
            context["skip_button"] = True
            context["message"] = {
                "alert-success": _("Your account has been created! \n Do you want to create your organisation now? "
                                   "You could do it later but it is required to do an evaluation.")
            }
        else:
            organisation_required_message(
                context
            )  # Add the message user need to create his organisation
            context["skip_button"] = False
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """If the form is valid, redirect to the supplied URL."""
        form = OrganisationCreationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            user = request.user
            name = form.cleaned_data.get("name")
            size = form.cleaned_data.get("size")
            country = form.cleaned_data.get("country")
            sector = form.cleaned_data.get("sector")
            # This method handles the fact that the membership is created for this orga as admin
            organisation = Organisation.create_organisation(
                name=name, size=size, country=country, sector=sector, created_by=user,
            )
            logger.info(f"[organisation_creation] A new organisation {organisation.name} has been created by "
                        f"the user {user.email}")
            # redirect to a new URL, evaluation creation if there is an assessment in the DB, else profile:
            if get_last_assessment_created():
                response = redirect("assessment:creation-evaluation", organisation.id)
            else:
                response = redirect("home:user-profile")
            return response
        else:
            return self.form_invalid(form)


# RESET PASSWORD #


class PasswordReset(auth_views.PasswordResetView):
    form_class = PasswordResetForm_  # Change the form because issue with is_active (and active in the User model)


# FUNCTIONS #


def manage_message_login_page(request):
    """
    This function manages the messages displayed to the user in the login page
    I have chosen to not use the Django messages process (messages.add_message) as it doesn't work properly
    :param request:
    :return:
    """
    previous_url = request.META.get("HTTP_REFERER")
    # Case it s a redirection because the user wanted to access content where as he is not login
    if previous_url is None:
        message = {
            # todo : solve bug translation
            "alert-danger": _("You must be connected to access this content")
        }
        return message  # break the function
    # Case the user failed to provide a good combination of email and password
    elif "/login/" in previous_url or previous_url == "http://127.0.0.1:8000/":  # todo will need to be changed
        message = {
            # todo : solve bug translation
            "alert-warning": _("The attempt to connect with this combination email/password failed. Please try again!")
        }

    # When signup is the previous page, the user has clicked on connexion button in the navbar after the login popin
    # process
    # Case "/signup/" in previous_url
    else:
        message = {
            # todo : solve bug translation
            " alert-info": _("Please, enter your email and your password to login to your account.\n "
                             "If you don't have an account, click on the 'I do not have an account' button")
        }
    return message


def organisation_required_message(context):
    """
    I do not use the django method to display messages as the front is to 'ugly' and I have an easier way to do this
    as long as there is only one message to display
    :param context:
    :return:
    """
    context["message"] = {
        # todo : solve bug translation
        "alert-warning": _("You first need to create your organisation before creating your evaluation.")
    }
