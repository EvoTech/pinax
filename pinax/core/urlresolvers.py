from __future__ import absolute_import, unicode_literals
from django.core import urlresolvers
from django.contrib.sites.models import Site
from django.conf import settings

# TODO: Fix me. Signal? Settings?


def reverse_full(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
                 current_app=None, firm=None, group=None, subdomain=None,
                 defaults=None):
    """Returns URL including host."""

    host = None
    url = None

    if kwargs is None:
        kwargs = {}
    if defaults is None:
        defaults = kwargs.pop('_defaults', {})
    if firm is None:
        firm = kwargs.pop('_firm', None)
    if group is None:
        group = firm or kwargs.pop('_group', None)
    if subdomain is None:
        subdomain = kwargs.pop('_subdomain', None)

    kwargs2 = defaults.copy()
    kwargs2.update(kwargs)
    
    for k in kwargs2.copy():
        if kwargs2[k] is None or kwargs2[k] == 'None':
            kwargs2.pop(k)
    kwargs = kwargs2

    if group:
        try:
            from firms.models import Firm
            if isinstance(group, Firm):
                host = group.get_host()
                if group.has_own_location():
                    urlconf = settings.ROOT_URLCONF_FIRM
        except ImportError:  # No firms module
            pass

        from groups.bridge import ContentBridge
        bridge = ContentBridge(group.__class__)
        try:
            url = bridge.reverse(viewname, group, kwargs, urlconf, prefix, current_app)
        except urlresolvers.NoReverseMatch:
            pass

    elif subdomain:
        urlconf = settings.ROOT_URLCONF_FIRM

    else:
        subdomain = getattr(settings, 'DEFAULT_SUBDOMAIN', 'www')
        urlconf = settings.ROOT_URLCONF

    if host is None:
        current_site = Site.objects.get_current()
        host = '{0}.{1}'.format(subdomain, current_site) if subdomain else current_site

    if url is None:
        url = urlresolvers.reverse(viewname, urlconf, args, kwargs, prefix, current_app)

    protocol = getattr(settings, 'DEFAULT_PROTOCOL', 'http')
    full_url = '{protocol}://{host}{path}'.format(
        protocol=protocol,
        host=host,
        path=url
    )
    return full_url
