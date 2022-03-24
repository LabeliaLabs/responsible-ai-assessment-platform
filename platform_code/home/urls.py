from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path, reverse_lazy
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


from .views import (
    HomepageView,
    activate,
    ProfileView,
    ProfileSettingsView,
    OrganisationCreationView,
    LogoutView,
    delete_user,
    export_user_data,
    PasswordReset,
    ResourcesView,
    ReleaseNotesView,
    DashboardView,
)


app_name = "home"
urlpatterns = [
    path("", HomepageView.as_view(), name="homepage"),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z\_\.\-]+)/$',
            activate,
            name='activate'
            ),
    path("release-notes/", ReleaseNotesView.as_view(), name="release-notes"),
    path("admin-dashboard/", DashboardView.as_view(), name="admin-dashboard"),
    re_path(r"admin-dashboard/(?P<tab>[a-z]{1,15})", DashboardView.as_view(), name="admin-dashboard"),
    path("robots.txt", TemplateView.as_view(
        template_name="robots.txt", content_type="text/plain"
    )),
    path(
        "accounts/",
        include(
            [
                path(r"profile/", ProfileView.as_view(), name="user-profile"),
                re_path(r"profile/(?P<tab>[a-z]{1,15})", ProfileView.as_view(), name="user-profile"),
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
                path(
                    "reset/<uidb64>/<token>/",
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
