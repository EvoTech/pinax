from django import template
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from avatar.templatetags.avatar_tags import avatar_url as avatar_url_orig,\
    avatar as avatar_orig, AVATAR_DEFAULT_URL

register = template.Library()


@register.simple_tag
def avatar_url(user, size=40):

    if not isinstance(user, User):
        try:
            user = User.objects.get(username=user, is_active=True)
        except User.DoesNotExist:
            return AVATAR_DEFAULT_URL
    return avatar_url_orig(user, size)


@register.simple_tag
def avatar(user, size=40):
    if not isinstance(user, User):
        try:
            user = User.objects.get(username=user, is_active=True)
            alt = unicode(user)
            url = avatar_url(user, size)
        except User.DoesNotExist:
            url = AVATAR_DEFAULT_URL
            alt = _("Default Avatar")
    else:
        alt = unicode(user)
        url = avatar_url(user, size)
    return """<img src="%s" alt="%s" width="%s" height="%s" />""" % (url, alt,
        size, size)
