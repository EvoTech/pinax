import re

from django.conf import settings
from django.core.exceptions import PermissionDenied

MASK_IN_EXCEPTION_EMAIL= ["password", "mail", "protected", "private"]
mask_re = re.compile("(" + "|".join(MASK_IN_EXCEPTION_EMAIL) + ")", re.I)


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


class GroupPrivateMiddleware(object):
    """Rejects access to private groups for non-members

    Should be after groups.middleware.GroupAwareMiddleware
    """
    def process_view(self, request, view, view_args, view_kwargs):
        """Raises PermissionDenied if user has not access to group."""
        group = getattr(request, 'group', None)
        if group is not None and getattr(group, 'private', False)\
                and not group.user_is_member(request.user)\
                and not request.user.has_perms('view', group):
            raise PermissionDenied
