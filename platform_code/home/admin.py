from django.contrib import admin
from django.contrib.auth.models import Group

from .admin_utils.dashboard_admin import DashboardAdminSite
from .admin_utils.organisation_admin import OrganisationAdmin
from .admin_utils.platform_management_admin import PlatformManagementAdmin
from .admin_utils.user_admin import UserAdmin
from .models import (
    UserResources,
    Organisation,
    Membership,
    User,
    PendingInvitation,
    PlatformManagement,
    ReleaseNote,
)

# Register your models here.

admin.site.register(PlatformManagement, PlatformManagementAdmin)
admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Membership)
admin.site.register(UserResources)
admin.site.register(PendingInvitation)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(ReleaseNote)

admin_dashboard = DashboardAdminSite(name='admin-dashboard')
