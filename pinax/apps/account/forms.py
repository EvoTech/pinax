from __future__ import absolute_import, unicode_literals
import re

from django import forms
from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.http import int_to_base36

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site

from captcha.fields import CaptchaField
from emailconfirmation.models import EmailAddress
from timezones.forms import TimeZoneField

from pinax.apps.account.models import Account, PasswordReset
from pinax.apps.account.utils import perform_login
from pinax.apps.account.conf import settings
from pinax.utils.make_agreement_form import make_agreement_form

alnum_re = re.compile(r"^\w+$")


class GroupForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop("group", None)
        super(GroupForm, self).__init__(*args, **kwargs)


class LoginForm(GroupForm):

    password = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    remember = forms.BooleanField(
        label = _("Remember Me"),
        help_text = _("If checked you will stay logged in for 3 weeks"),
        required = False
    )
    
    user = None
    
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        ordering = []
        if settings.EMAIL_AUTHENTICATION:
            self.fields["email"] = forms.EmailField(
                label = ugettext("E-mail"),
            )
            ordering.append("email")
        else:
            self.fields["username"] = forms.CharField(
                label = ugettext("Username"),
                max_length = 30,
            )
            ordering.append("username")
        ordering.extend(["password", "remember"])
        self.fields.keyOrder = ordering
    
    def user_credentials(self):
        """
        Provides the credentials required to authenticate the user for
        login.
        """
        credentials = {}
        if settings.EMAIL_AUTHENTICATION:
            credentials["email"] = self.cleaned_data["email"]
        else:
            credentials["username"] = self.cleaned_data["username"]
        credentials["password"] = self.cleaned_data["password"]
        return credentials
    
    def clean(self):
        if self._errors:
            return
        user = authenticate(**self.user_credentials())
        if user and not user.username.startswith("__"):
            if user.is_active:
                self.user = user
            else:
                raise forms.ValidationError(_("This account is currently inactive."))
        else:
            if settings.EMAIL_AUTHENTICATION:
                error = _("The e-mail address and/or password you specified are not correct.")
            else:
                error = _("The username and/or password you specified are not correct.")
            raise forms.ValidationError(error)
        return self.cleaned_data
    
    def login(self, request):
        perform_login(request, self.user)
        if self.cleaned_data["remember"]:
            request.session.set_expiry(60 * 60 * 24 * 7 * 3)
        else:
            request.session.set_expiry(0)


class SignupFormBase(GroupForm):
    
    username = forms.CharField(
        label = _("Username"),
        max_length = 30,
        widget = forms.TextInput()
    )
    password1 = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    email = forms.EmailField(widget=forms.TextInput())
    confirmation_key = forms.CharField(
        max_length = 40,
        required = False,
        widget = forms.HiddenInput()
    )
    captcha = CaptchaField()
    
    def __init__(self, *args, **kwargs):
        super(SignupFormBase, self).__init__(*args, **kwargs)
        if settings.REQUIRED_EMAIL or settings.EMAIL_VERIFICATION or settings.EMAIL_AUTHENTICATION:
            self.fields["email"].label = ugettext("E-mail")
            self.fields["email"].required = True
        else:
            self.fields["email"].label = ugettext("E-mail (optional)")
            self.fields["email"].required = False
    
    def clean_username(self):
        if self.cleaned_data["username"].startswith("__"):
            # Prefix "__" or "__NUMBER_" e.g. "__3_" reserved for marked as removed users.
            raise forms.ValidationError(_("Usernames can't starts with double underscore."))
        if not alnum_re.search(self.cleaned_data["username"]):
            raise forms.ValidationError(_("Usernames can only contain letters, numbers and underscores."))
        try:
            user = User.objects.get(username__iexact=self.cleaned_data["username"])
        except User.DoesNotExist:
            return self.cleaned_data["username"]
        raise forms.ValidationError(_("This username is already taken. Please choose another."))
    
    def clean_email(self):
        value = self.cleaned_data["email"]
        if value.startswith("__"):
            # Prefix "__" or "__NUMBER_" e.g. "__3_" reserved for marked as removed users.
            # TODO: Add ability to restore account what was marked as deleted.
            raise forms.ValidationError(_("Email can't starts with double underscore."))
        if settings.UNIQUE_EMAIL or settings.EMAIL_AUTHENTICATION:
            try:
                User.objects.get(email__iexact=value)
            except User.DoesNotExist:
                return value
            raise forms.ValidationError(_("A user is registered with this e-mail address."))
        return value
    
    def clean(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data
    
    def create_user(self, username=None, commit=True):
        user = User()
        if username is None:
            raise NotImplementedError("SignupForm.create_user does not handle "
                "username=None case. You must override this method.")
        user.username = username
        user.email = self.cleaned_data["email"].strip().lower()
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user
    
    def login(self, request, user):
        # nasty hack to get get_user to work in Django
        user.backend = django_settings.AUTHENTICATION_BACKENDS[0]
        perform_login(request, user)
    
    def save(self, request=None):
        # don't assume a username is available. it is a common removal if
        # site developer wants to use e-mail authentication.
        username = self.cleaned_data.get("username")
        email = self.cleaned_data["email"]
        
        if self.cleaned_data["confirmation_key"]:
            from friends.models import JoinInvitation # @@@ temporary fix for issue 93
            try:
                join_invitation = JoinInvitation.objects.get(confirmation_key=self.cleaned_data["confirmation_key"])
                confirmed = True
            except JoinInvitation.DoesNotExist:
                confirmed = False
        else:
            confirmed = False
        
        # @@@ clean up some of the repetition below -- DRY!
        
        if confirmed:
            if email == join_invitation.contact.email:
                new_user = self.create_user(username)
                join_invitation.accept(new_user) # should go before creation of EmailAddress below
                if request:
                    messages.add_message(request, messages.INFO,
                        ugettext("Your e-mail address has already been verified")
                    )
                # already verified so can just create
                EmailAddress(user=new_user, email=email, verified=True, primary=True).save()
            else:
                new_user = self.create_user(username)
                join_invitation.accept(new_user) # should go before creation of EmailAddress below
                if email:
                    if request:
                        messages.add_message(request, messages.INFO,
                            ugettext("Confirmation e-mail sent to %(email)s") % {
                                "email": email,
                            }
                        )
                    EmailAddress.objects.add_email(new_user, email)
        else:
            new_user = self.create_user(username)
            if email:
                if request and not settings.EMAIL_VERIFICATION:
                    messages.add_message(request, messages.INFO,
                        ugettext("Confirmation e-mail sent to %(email)s") % {
                            "email": email,
                        }
                    )
                EmailAddress.objects.add_email(new_user, email)
        
        if settings.EMAIL_VERIFICATION:
            new_user.is_active = False
            new_user.save()
        
        self.after_signup(new_user)
        
        return new_user
    
    def after_signup(self, user, **kwargs):
        """
        An extension point for subclasses.
        """
        pass

SignupForm = make_agreement_form(SignupFormBase)


class UserForm(forms.Form):
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)


class AccountForm(UserForm):
    
    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        try:
            self.account = Account.objects.get(user=self.user)
        except Account.DoesNotExist:
            self.account = Account(user=self.user)


class AddEmailFormBase(UserForm):
    
    email = forms.EmailField(
        label = _("E-mail"),
        required = True,
        widget = forms.TextInput(attrs={"size": "30"})
    )
    
    def clean_email(self):
        value = self.cleaned_data["email"]
        errors = {
            "this_account": _("This e-mail address already associated with this account."),
            "different_account": _("This e-mail address already associated with another account."),
        }
        if settings.UNIQUE_EMAIL:
            try:
                email = EmailAddress.objects.get(email__iexact=value)
            except EmailAddress.DoesNotExist:
                return value
            if email.user == self.user:
                raise forms.ValidationError(errors["this_account"])
            raise forms.ValidationError(errors["different_account"])
        else:
            try:
                EmailAddress.objects.get(user=self.user, email__iexact=value)
            except EmailAddress.DoesNotExist:
                return value
            raise forms.ValidationError(errors["this_account"])
    
    def save(self):
        return EmailAddress.objects.add_email(self.user, self.cleaned_data["email"])

AddEmailForm = make_agreement_form(AddEmailFormBase)


class ChangePasswordForm(UserForm):
    
    oldpassword = forms.CharField(
        label = _("Current Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password1 = forms.CharField(
        label = _("New Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("New Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    
    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError(_("Please type your current password."))
        return self.cleaned_data["oldpassword"]
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save()


class SetPasswordForm(UserForm):
    
    password1 = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save()


class ResetPasswordForm(forms.Form):
    
    email = forms.EmailField(
        label = _("E-mail"),
        required = True,
        widget = forms.TextInput(attrs={"size":"30"})
    )
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        if settings.EMAIL_VERIFICATION_PASSWORD_RESET and EmailAddress.objects.filter(email__iexact=email, verified=True).count() == 0:
            raise forms.ValidationError(_("Email address not verified for any user account"))
        if not EmailAddress.objects.filter(email__iexact=email).exists():
            exists = False
            for user in User.objects.filter(email__iexact=email):
                EmailAddress.objects.add_email(user, user.email)
                exists = True
            if not exists:
                raise forms.ValidationError(_("Email address not exists for any user account"))
        return email
    
    def save(self, **kwargs):
        
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", default_token_generator)
        
        for user in User.objects.filter(email__iexact=email):
            
            temp_key = token_generator.make_token(user)
            
            # save it to the password reset model
            password_reset = PasswordReset(user=user, temp_key=temp_key)
            password_reset.save()
            
            current_site = Site.objects.get_current()
            domain = str(current_site.domain)
            
            # send the password reset email
            subject = _("[%s] Password reset e-mail sent") % domain
            message = render_to_string("account/password_reset_key_message.txt", {
                "user": user,
                "uid": int_to_base36(user.id),
                "temp_key": temp_key,
                "domain": domain,
            })
            send_mail(subject, message, django_settings.DEFAULT_FROM_EMAIL, [user.email])
        return self.cleaned_data["email"]


class ResetPasswordKeyForm(forms.Form):
    
    password1 = forms.CharField(
        label = _("New Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("New Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.temp_key = kwargs.pop("temp_key", None)
        super(ResetPasswordKeyForm, self).__init__(*args, **kwargs)
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        # set the new user password
        user = self.user
        user.set_password(self.cleaned_data["password1"])
        user.save()
        # mark password reset object as reset
        PasswordReset.objects.filter(temp_key=self.temp_key).update(reset=True)


class ChangeTimezoneForm(AccountForm):
    
    timezone = TimeZoneField(label=_("Timezone"), required=True)
    
    def __init__(self, *args, **kwargs):
        super(ChangeTimezoneForm, self).__init__(*args, **kwargs)
        self.initial.update({"timezone": self.account.timezone})
    
    def save(self):
        self.account.timezone = self.cleaned_data["timezone"]
        self.account.save()


class ChangeLanguageForm(AccountForm):
    
    language = forms.ChoiceField(
        label = _("Language"),
        required = True,
        choices = django_settings.LANGUAGES
    )
    
    def __init__(self, *args, **kwargs):
        super(ChangeLanguageForm, self).__init__(*args, **kwargs)
        self.initial.update({"language": self.account.language})
    
    def save(self):
        self.account.language = self.cleaned_data["language"]
        self.account.save()
