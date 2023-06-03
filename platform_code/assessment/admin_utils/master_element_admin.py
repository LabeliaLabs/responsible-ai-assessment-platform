from django.contrib import admin


class MasterEvaluationElementAdmin(admin.ModelAdmin):
    """ """

    list_display = (
        "id",
        "numbering",
        "get_name",
        "get_master_section",
        "question_type",
        "get_depends_on",
        "has_resources",
    )
    list_filter = (
        "master_section",
        "master_section__assessment__version",
    )

    def get_name(self, obj):
        return "Master element : " + obj.name

    def get_master_section(self, obj):
        if obj.master_section:
            return str(obj.master_section)[:25]
        else:
            return None

    def get_depends_on(self, obj):
        if obj.depends_on:
            return obj.depends_on.get_numbering()
        else:
            return None

    def has_resources(self, obj):
        return obj.has_resources()

    def numbering(self, obj):
        return obj.get_numbering()
