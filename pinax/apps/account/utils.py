from __future__ import absolute_import, unicode_literals
from django.conf import settings

from django.contrib.auth import login
from django.utils.translation import ugettext_lazy as _

from pinax.apps.account.signals import user_logged_in


def get_default_redirect(request, fallback_url, redirect_field_name="next", session_key_value="redirect_to"):
    """
    Returns the URL to be used in login procedures by looking at different
    values in the following order:
    
    - a REQUEST value, GET or POST, named "next" by default.
    - LOGIN_REDIRECT_URL - the URL in the setting
    - LOGIN_REDIRECT_URLNAME - the name of a URLconf entry in the settings
    """
    redirect_to = request.REQUEST.get(redirect_field_name)
    if not redirect_to:
        # try the session if available
        if hasattr(request, "session"):
            redirect_to = request.session.get(session_key_value)
    # light security check -- make sure redirect_to isn't garabage.
    if not redirect_to or "://" in redirect_to or " " in redirect_to:
        redirect_to = fallback_url
    return redirect_to


def user_display(user):
    func = getattr(settings, "ACCOUNT_USER_DISPLAY", lambda user: user.username)
    try:
        if user is None:
            return _("deleted user")
        if user.username.startswith("__"):
            # Prefix "__" or "__NUMBER_" e.g. "__3_" reserved for marked as removed users.
            return _("deleted user")
        if not user.is_active:
            return _("inactive user")
        return func(user)
    except AttributeError:
        return _("deleted user")


def perform_login(request, user):
    user_logged_in.send(sender=user.__class__, request=request, user=user)
    login(request, user)
