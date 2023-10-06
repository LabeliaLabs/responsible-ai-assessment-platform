from django.contrib import admin
from home.models import PlatformText


class PlatformTextAdmin(admin.ModelAdmin):
    """ """

    fieldsets = (
        (
            "Homepage",
            {
                "fields": (
                    "homepage_text",
                    "homepage_text_fr",
                    "homepage_text_en",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        """
        Can only have one platform text object
        """
        return len(list(PlatformText.objects.all())) == 0

    def has_delete_permission(self, request, obj=None):
        """
        Cannot delete platform text object
        """
        return False
