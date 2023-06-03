from django.contrib import admin
from home.models import PlatformManagement


class PlatformManagementAdmin(admin.ModelAdmin):
    """
    Manage the actions on the platform management object (unique)
    """

    def has_add_permission(self, request):
        """
        Can only have one platform management object
        """
        return len(list(PlatformManagement.objects.all())) == 0

    def has_delete_permission(self, request, obj=None):
        """
        Cannot delete platform management object
        """
        return False
