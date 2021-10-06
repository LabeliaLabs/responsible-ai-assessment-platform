from django.contrib import admin


class LabellingAdmin(admin.ModelAdmin):
    """
    Defines the admin panel for the labelling objects
    """
    list_display = (
        "evaluation",
        "get_organisation",
        "status",
        "counter",
        "start_date",
        "last_update",
    )
    list_filter = (
        "status",
        "evaluation",
    )

    def get_organisation(self, obj):
        return obj.evaluation.organisation
