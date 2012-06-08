from django import forms
from django.conf import settings

from pinax.apps.account.forms import GroupForm, SignupForm as BaseSignupForm
from pinax.apps.signup_codes.models import SignupCode, check_signup_code

DEFAULT_SIGNUP_CODE_EXPIRY = 7 * 24  # hours
SIGNUP_CODE_EXPIRY = getattr(settings, 'SIGNUP_CODE_EXPIRY',
                             DEFAULT_SIGNUP_CODE_EXPIRY)


class SignupForm(BaseSignupForm):
    
    signup_code = forms.CharField(max_length=40, required=False, widget=forms.HiddenInput())
    
    def clean_signup_code(self):
        code = self.cleaned_data.get("signup_code")
        signup_code = check_signup_code(code)
        if signup_code:
            return signup_code
        else:
            raise forms.ValidationError("Signup code was not valid.")


class InviteUserForm(GroupForm):
    
    email = forms.EmailField()
    
    def create_signup_code(self, commit=True):
        email = self.cleaned_data["email"]
        signup_code = SignupCode.create(email, SIGNUP_CODE_EXPIRY,
                                        group=self.group)
        if commit:
            signup_code.save()
        return signup_code
    
    def send_signup_code(self):
        signup_code = self.create_signup_code()
        signup_code.send()
