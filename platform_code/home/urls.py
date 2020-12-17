from django.urls import path, include, re_path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import (
    LoginView,
    signup,
    activate,
    legal_notices_view,
    faq_view,
    ProfileView,
    ProfileSettingsView,
    OrganisationCreationView,
    LogoutView,
    delete_user,
    export_user_data,
    PasswordReset,
    ResourcesView,
    LoginPageView
)


app_name = "home"
urlpatterns = [
    path("", LoginView.as_view(), name="homepage"),
    path("signup/", signup, name="signup"),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z\_\.\-]+)/$',
            activate,
            name='activate'
            ),
    path("login/", LoginPageView.as_view(), name="login"),  # login page when redirect
    path("legal-notices/", legal_notices_view, name="legal-notices"),
    path("faq/", faq_view, name="faq"),
    path(
        "accounts/",
        include(
            [
                path("profile/", ProfileView.as_view(), name="user-profile"),
                path(
                    "profile-settings/",
                    ProfileSettingsView.as_view(),
                    name="user-profile-settings",
                ),
                path(
                    "organisation-creation/",
                    OrganisationCreationView.as_view(),
                    name="orga-creation",
                ),  # when its not a pop in
                path("logout/", LogoutView.as_view(), name="logout"),
                path("delete-user", delete_user, name="delete-user"),
                path(
                    "export-user-data", export_user_data, name="export-user-data"
                ),
                path("ressources/", ResourcesView.as_view(), name="resources"),
                re_path(
                    r"^password_reset/$",
                    PasswordReset.as_view(
                        template_name="home/registration/password_reset_form.html",
                        email_template_name="home/registration/password_reset_email.html",
                        success_url=reverse_lazy("home:password_reset_done"),
                        subject_template_name="home/registration/password_reset_subject.html",
                    ),
                    name="password_reset",
                ),
                re_path(
                    r"^password_reset/done/$",
                    auth_views.PasswordResetDoneView.as_view(
                        template_name="home/registration/password_reset_done.html"
                    ),
                    name="password_reset_done",
                ),
                re_path(
                    r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
                    auth_views.PasswordResetConfirmView.as_view(
                        template_name="home/registration/password_reset_confirm.html",
                        success_url=reverse_lazy("home:password_reset_complete"),
                    ),
                    name="password_reset_confirm",
                ),
                re_path(
                    r"^reset/done/$",
                    auth_views.PasswordResetCompleteView.as_view(
                        template_name="home/registration/password_reset_complete.html"
                    ),
                    name="password_reset_complete",
                ),
            ]
        ),
    ),
]
