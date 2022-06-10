from django.contrib import admin


class MasterSectionAdmin(admin.ModelAdmin):
    """

    """
    list_display = (
        "id",
        "numbering",
        "get_name",
        "assessment",
        "number_of_elements"
    )
    list_filter = (
        "assessment__version",
    )

    def get_name(self, obj):
        return "Master section : " + obj.name

    def numbering(self, obj):
        return obj.get_numbering()

    def number_of_elements(self, obj):
        return len(obj.masterevaluationelement_set.all())
