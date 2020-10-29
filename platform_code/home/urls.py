from django.urls import path, include, re_path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = "home"
urlpatterns = [
    path("", views.LoginView.as_view(), name="homepage"),
    path("signup/", views.signup, name="signup"),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z\_\.\-]+)/$',
            views.activate,
            name='activate'
            ),
    path("login/", views.login_view, name="login"),  # login page when redirect
    path("about/", views.about_view, name="about"),
    path("legal-notices/", views.legal_notices_view, name="legal-notices"),
    path(
        "accounts/",
        include(
            [
                path("profile/", views.ProfileView.as_view(), name="user-profile"),
                path(
                    "profile-settings/",
                    views.ProfileSettingsView.as_view(),
                    name="user-profile-settings",
                ),
                path(
                    "organisation-creation/",
                    views.OrganisationCreationView.as_view(),
                    name="orga-creation",
                ),  # when its not a pop in
                path("logout/", views.LogoutView.as_view(), name="logout"),
                path("delete-user", views.delete_user, name="delete-user"),
                path(
                    "export-user-data", views.export_user_data, name="export-user-data"
                ),
                path("ressources/", views.ResourcesView.as_view(), name="resources"),
                re_path(
                    r"^password_reset/$",
                    views.PasswordReset.as_view(
                        template_name="home/registration/password_reset_form.html",
                        email_template_name="home/registration/password_reset_email.html",
                        success_url=reverse_lazy("home:password_reset_done"),
                        subject_template_name="home/registration/password_reset_subject.txt",
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
