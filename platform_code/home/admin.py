from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import UserResources, Organisation, Membership, User
from .forms import UserAdminCreationForm, UserAdminChangeForm

# Register your models here.

admin.site.register(Organisation)
admin.site.register(Membership)
admin.site.register(UserResources)


# USER PART #


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        "email",
        "admin",
        "active",
        "first_name",
        "last_name",
    )
    list_filter = ("admin",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name",)}),
        ("Permissions", {"fields": ("admin",)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("email",)
    filter_horizontal = ()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_admin = request.user.admin

        # Security to just allow admin to change this field
        if not is_admin:
            form.base_fields["admin"].disabled = True
            form.base_fields["email"].disabled = True

            # Prevent non-superusers from editing their own permissions
            if not is_admin and obj is not None and obj == request.user:
                form.base_fields["staff"].disabled = True
                form.base_fields["admin"].disabled = True
                form.base_fields["groups"].disabled = True
                form.base_fields["user_permissions"].disabled = True

        return form


admin.site.register(User, UserAdmin)


# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)
