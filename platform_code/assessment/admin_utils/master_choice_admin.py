from django.contrib import admin


class MasterChoiceAdmin(admin.ModelAdmin):
    """

    """
    list_display = (
        "id",
        "numbering",
        "get_name",
        "get_master_evaluation_element",
        "is_concerned_switch",
        "get_master_evaluation_elements_depending_on",

    )
    list_filter = (
        "master_evaluation_element",
        "master_evaluation_element__master_section__assessment__version",
    )

    def get_name(self, obj):
        return "Master choice: " + obj.answer_text[:25]

    def get_master_evaluation_element(self, obj):
        if obj.master_evaluation_element:
            return str(obj.master_evaluation_element)[:25]
        else:
            return None

    def numbering(self, obj):
        return obj.get_numbering()

    def get_master_evaluation_elements_depending_on(self, obj):
        return obj.get_list_master_element_depending_on()
