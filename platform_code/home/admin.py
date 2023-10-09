from django.contrib import admin
from django.contrib.auth.models import Group

from .admin_utils.dashboard_admin import DashboardAdminSite
from .admin_utils.organisation_admin import OrganisationAdmin
from .admin_utils.platfom_text_admin import PlatformTextAdmin
from .admin_utils.platform_management_admin import PlatformManagementAdmin
from .admin_utils.user_admin import UserAdmin
from .models import (
    Footer,
    Membership,
    Organisation,
    PendingInvitation,
    PlatformManagement,
    PlatformText,
    ReleaseNote,
    User,
    UserResources,
)


class MembershipAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "get_organisation_name", "role")
    list_filter = (
        "role",
        "user",
        "organisation",
    )

    @admin.display(description="Organisation")
    def get_organisation_name(self, instance):
        return instance.organisation.name


class PendingInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "email",
        "get_organisation_name",
        "role",
    )
    list_filter = (
        "organisation",
        "role",
    )

    @admin.display(description="Organisation")
    def get_organisation_name(self, instance):
        return instance.organisation.name


class FooterAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


admin.site.register(PlatformManagement, PlatformManagementAdmin)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(UserResources)
admin.site.register(PendingInvitation, PendingInvitationAdmin)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(ReleaseNote)
admin.site.register(Footer, FooterAdmin)
admin.site.register(PlatformText, PlatformTextAdmin)

admin_dashboard = DashboardAdminSite(name="admin-monitoring")
