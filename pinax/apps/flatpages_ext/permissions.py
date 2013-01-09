from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site

import authority
from authority.permissions import BasePermission


class FlatPagePermission(BasePermission):
    """FlatPage permissions"""
    label = 'flatpage_permission'

    def has_perm(self, perm, obj, check_groups=True, approved=True):
        """Checks with recursion if user has the permission

        for the given object
        """
        perm = super(FlatPagePermission, self).has_perm(
            perm, obj, check_groups, approved
        )
        if perm is not None:
            return perm

        sep = '/'
        parts = obj.url.rstrip(sep).split(sep)
        parts.pop()
        site_id = Site.objects.get_current().id
        while len(parts) > 0:
            parent = None
            url = sep.join(parts)
            try:
                parent = FlatPage.objects.get(
                    url__exact=url,
                    sites__id__exact=site_id
                )
            except FlatPage.DoesNotExist:
                if not url.endswith(sep) and settings.APPEND_SLASH:
                    url += sep
                try:
                    parent = FlatPage.objects.get(
                        url__exact=url,
                        sites__id__exact=site_id
                    )
                except FlatPage.DoesNotExist:
                    pass

            if parent:
                perm = super(FlatPagePermission, self).has_perm(
                    perm, parent, check_groups, approved
                )
                if perm is not None:
                    return perm
            parts.pop()
        return None


authority.register(FlatPage, FlatPagePermission)
