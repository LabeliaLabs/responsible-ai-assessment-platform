from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from home.forms import UserAdminCreationForm, UserAdminChangeForm


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
        "staff",
        "active",
        "first_name",
        "last_name",
        "get_created_at",
        "get_last_login",
        "language_preference",
        "organisations_user_is_member",
    )
    readonly_fields = ["created_at", "last_login"]
    list_filter = (
        "admin",
        "staff",
        "created_at",
        "active",
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name",)}),
        ("Permissions", {"fields": ("admin",)}),
        ("Creation and connexions", {"fields": ("created_at", "last_login",)}),
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

    def get_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%d/%m/%Y")
        else:
            return "No date"

    def get_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime("%d/%m/%Y")
        else:
            return "Not logged yet"

    def organisations_user_is_member(self, obj):
        """
        Return the string of the organisations names where the user is member,
        regardless the role, but it just doesn't count the admin users
        who are automatically members.
        """
        membership_list = obj.membership_set.all().filter(hide_membership=False)
        return ', '.join([membership.organisation.name for membership in membership_list])

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
