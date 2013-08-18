from __future__ import absolute_import, unicode_literals
from django import template

register = template.Library()


@register.inclusion_tag("profile_item.html")
def show_profile(user):
    return {"user": user}


@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if "search" in getvars:
        del getvars["search"]
    if len(list(getvars.keys())) > 0:
        return "{0}?{1}".format(request.path, getvars.urlencode())
    else:
        return request.path
