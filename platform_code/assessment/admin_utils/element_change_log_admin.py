from django.contrib import admin, messages
from django.shortcuts import redirect


class ElementChangeLogAdmin(admin.ModelAdmin):
    """
    This class manages the element change log table on the admin page
    """
    list_display = ("eval_element_numbering",
                    "assessment",
                    "previous_assessment",
                    "pastille",
                    "edito",
                    "visibility",
                    )

    list_filter = (
        "eval_element_numbering",
        "assessment",
        "previous_assessment",
        "pastille",
        "edito",
        "visibility",
    )
    actions = [
        'hide_change_log',
        'display_change_log',
    ]

    def hide_change_log(self, request, queryset):
        for change_log in queryset:
            try:
                change_log.hide()
                self.message_user(request, f"The change log {change_log} is now hidden!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when hiding the change log {change_log}",
                    messages.ERROR
                )
        return redirect(request.path_info)

    def display_change_log(self, request, queryset):
        for change_log in queryset:
            try:
                change_log.display()
                self.message_user(request, f"The change log {change_log} is now visible!", messages.SUCCESS)
            except Exception as e:
                self.message_user(
                    request,
                    f"An error occurred, {e}, when hiding the change log {change_log}",
                    messages.ERROR
                )
        return redirect(request.path_info)
