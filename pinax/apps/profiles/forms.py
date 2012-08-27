from __future__ import absolute_import, unicode_literals
from django import forms

from pinax.apps.profiles.models import Profile
from pinax.utils.make_agreement_form import make_agreement_form


class ProfileFormBase(forms.ModelForm):
    
    class Meta:
        model = Profile
        exclude = [
            "user",
            "blogrss",
            "timezone",
            "language",
            "twitter_user",
            "twitter_password",
        ]

ProfileForm = make_agreement_form(ProfileFormBase)
