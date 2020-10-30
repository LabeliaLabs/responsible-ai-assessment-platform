from django import forms
from django.utils.translation import gettext as _

from home.models import Membership


class AddMemberForm(forms.Form):
    """
    This form is used to add a new member to the organisation
    """
    email = forms.EmailField(max_length=254,
                             widget=forms.Select(attrs={'class': 'full-width'}),
                             )
    role = forms.ChoiceField(choices=Membership.ROLES,
                             label=_("rights"),
                             initial="read_only",
                             widget=forms.Select(attrs={'class': 'full-width'})
                             )


class EditRoleForm(forms.Form):
    """
    This form is used to edit the role of members/invitations in an organisation
    """
    role = forms.ChoiceField(choices=Membership.ROLES,
                             label=_("rights"),
                             widget=forms.Select(attrs={'class': 'full-width'})
                             )

    def __init__(self, *args, **kwargs):
        is_member = False
        is_invitation = False
        if "member" in kwargs:
            member = kwargs.pop("member")
            is_member = True
        elif "invitation" in kwargs:
            invitation = kwargs.pop("invitation")
            is_invitation = True
        else:
            member = None
        super(EditRoleForm, self).__init__(*args, **kwargs)
        if is_member:
            self.fields["role"].initial = member.role
        if is_invitation:
            self.fields["role"].initial = invitation.role
