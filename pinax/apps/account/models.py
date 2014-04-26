from __future__ import absolute_import, unicode_literals
import sys

from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import get_language_from_request, get_language, ugettext_lazy as _

from django.contrib.auth.models import User, AnonymousUser

from emailconfirmation.models import EmailAddress, EmailConfirmation
from emailconfirmation.signals import email_confirmed
from timezones.fields import TimeZoneField

try:
    str = unicode  # Python 2.* compatible
except NameError:
    pass



class Account(models.Model):
    
    user = models.ForeignKey(User, unique=True, verbose_name=_("user"))
    
    timezone = TimeZoneField(_("timezone"))
    language = models.CharField(_("language"),
        max_length = 10,
        choices = settings.LANGUAGES,
        default = get_language
    )
    
    def __str__(self):
        return self.user.username


def create_account(sender, instance=None, **kwargs):
    if instance is None:
        return
    account, created = Account.objects.get_or_create(
        user=instance,
        defaults={'language': get_language(), }
    )


post_save.connect(create_account, sender=User)


# @@@ move to emailconfirmation app?
def superuser_email_address(sender, instance=None, **kwargs):
    if instance is None:
        return
    # only run when we are in syncdb or createsuperuser to be as unobstrusive
    # as possible and reduce the risk of running at inappropriate times
    if "syncdb" in sys.argv or "createsuperuser" in sys.argv:
        defaults = {
            "user": instance,
            "verified": True,
            "primary": True,
        }
        EmailAddress.objects.get_or_create(email=instance.email, **defaults)


post_save.connect(superuser_email_address, sender=User)


class AnonymousAccount(object):
    
    def __init__(self, request=None):
        self.user = AnonymousUser()
        self.timezone = settings.TIME_ZONE
        if request is not None:
            self.language = get_language_from_request(request)
        else:
            self.language = settings.LANGUAGE_CODE
    
    def __str__(self):
        return "AnonymousAccount"


class PasswordReset(models.Model):
    
    user = models.ForeignKey(User, verbose_name=_("user"))
    
    temp_key = models.CharField(_("temp_key"), max_length=100)
    timestamp = models.DateTimeField(_("timestamp"), default=datetime.now)
    reset = models.BooleanField(_("reset yet?"), default=False)
    
    def __str__(self):
        return "{0} (key={1}, reset={2})".format(
            self.user.username,
            self.temp_key,
            self.reset
        )


def mark_user_active(sender, instance=None, **kwargs):
    user = kwargs.get("email_address").user
    user.is_active = True
    user.save()


email_confirmed.connect(mark_user_active, sender=EmailConfirmation)

# Python 2.* compatible
try:
    unicode
except NameError:
    pass
else:
    for cls in (Account, AnonymousAccount, PasswordReset, ):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
