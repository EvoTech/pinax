from __future__ import absolute_import, unicode_literals
from django import template
from pinax.apps.projects.forms import ProjectForm



register = template.Library()



@register.inclusion_tag("projects/project_item.html", takes_context=True)
def show_project(context, project):
    return {"project": project, "request": context["request"]}


# @@@ should move these next two as they aren't particularly project-specific


@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if "search" in getvars:
        del getvars["search"]
    if len(list(getvars.keys())) > 0:
        return "{0}?{1}".format(request.path, getvars.urlencode())
    else:
        return request.path


@register.simple_tag
def persist_getvars(request):
    getvars = request.GET.copy()
    if len(list(getvars.keys())) > 0:
        return "?{0}".format(getvars.urlencode())
    return ""
