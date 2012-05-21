import re

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import resolve

MASK_IN_EXCEPTION_EMAIL = ["password", "mail", "protected", "private"]
mask_re = re.compile("(" + "|".join(MASK_IN_EXCEPTION_EMAIL) + ")", re.I)


DEFAULT_LOGIN_REQUIRE_URL_EXCEPTIONS = [
    "acct_login",
    "acct_signup",
    "acct_confirm_email",
    "acct_passwd_reset",
    "acct_passwd_reset_done",
    "acct_passwd_reset_key",
    "captcha-image",
    "captcha-audio",
]

DEFAULT_LOGIN_REQUIRE_REGEXP_EXCEPTIONS = []

LOGIN_REQUIRE_URL_EXCEPTIONS = getattr(
    settings,
    'LOGIN_REQUIRE_URL_EXCEPTIONS',
    DEFAULT_LOGIN_REQUIRE_URL_EXCEPTIONS
)

LOGIN_REQUIRE_REGEXP_EXCEPTIONS = getattr(
    settings,
    'LOGIN_REQUIRE_REGEXP_EXCEPTIONS',
    DEFAULT_LOGIN_REQUIRE_REGEXP_EXCEPTIONS
)


class HideSensistiveFieldsMiddleware(object):
    """
    A middleware that masks sensitive fields when an exception occurs,
    e.g. passwords in login attempts.
    """
    def process_exception(self, request, exception):
        if not request or not request.POST or settings.DEBUG:
            return None
        masked = False
        mutable = True
        if hasattr(request.POST, "_mutable"):
            mutable = request.POST._mutable
            request.POST._mutable = True
        for name in request.POST:
            if mask_re.search(name):
                request.POST[name] = u"xxHIDDENxx"
                masked = True
        if hasattr(request.POST, "_mutable"):
            request.POST._mutable = mutable


class LoginRequireEverywhereMiddleware(object):
    """Whole site requires login middleware."""
    def __init__(self):
        """Constructor."""
        self.url_exceptions = LOGIN_REQUIRE_URL_EXCEPTIONS
        self.regexp_exceptions = [re.compile(url) for url in LOGIN_REQUIRE_REGEXP_EXCEPTIONS]

    def process_request(self, request):
        """Determines, is current path require login."""
        if hasattr(request, 'user') and request.user.is_authenticated():
            return None
        # Looking by url names
        match = resolve(request.path_info)
        if match.view_name in self.url_exceptions:
            return None
        # Looking by regexp matching
        for url in self.regexp_exceptions:
            if url.match(request.path_info):
                return None
        return redirect_to_login(request.get_full_path())


class GroupPrivateMiddleware(object):
    """Rejects access to private groups for non-members

    Should be after groups.middleware.GroupAwareMiddleware
    """
    def process_view(self, request, view, view_args, view_kwargs):
        """Raises PermissionDenied if user has not access to group."""
        group = getattr(request, 'group', None)
        if group is not None and getattr(group, 'private', False)\
                and not request.user.has_perm('view', group):
            raise PermissionDenied
