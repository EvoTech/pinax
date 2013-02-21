from __future__ import absolute_import, unicode_literals
from django import template
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from avatar.templatetags.avatar_tags import avatar_url as avatar_url_orig,\
    avatar as avatar_orig, AVATAR_DEFAULT_URL

try:
    str = unicode  # Python 2.* compatible
except NameError:
    pass

register = template.Library()


@register.simple_tag
def avatar_url(user, size=40):
    """Returns avatar UPL only for active users."""
    if not isinstance(user, User):
        try:
            user = User.objects.get(username=user, is_active=True)
        except User.DoesNotExist:
            return AVATAR_DEFAULT_URL
    return avatar_url_orig(user, size)


@register.simple_tag
def avatar(user, size=40):
    """Returns avatar HTML only for active users."""
    if not isinstance(user, User):
        try:
            user = User.objects.get(username=user, is_active=True)
            alt = str(user)
            url = avatar_url(user, size)
        except User.DoesNotExist:
            url = AVATAR_DEFAULT_URL
            alt = _("Default Avatar")
    else:
        alt = str(user)
        url = avatar_url(user, size)
    return """<img src="{0}" alt="{1}" width="{2}" height="{3}" />""".format(
        url, alt, size, size
    )
