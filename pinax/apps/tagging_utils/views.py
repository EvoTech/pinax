from __future__ import absolute_import, unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model
from django.http import HttpResponse, Http404
from django.utils import simplejson

from tagging.models import Tag


def autocomplete(request, app_label, model):
    try:
        model = ContentType.objects.get(app_label=app_label, model=model)
    except:
        raise Http404

    if "term" not in request.GET:
        raise Http404
    else:
        q = request.GET["term"]

    try:
        limit = int(request.GET["limit"])
    except (KeyError, ValueError):
        limit = 10

    if limit > 100:
        limit = 100

    tags = Tag.objects.values_list("name", flat=True).filter(
        items__content_type = model,
        name__istartswith = q
    ).distinct().order_by("name")[:limit]

    return HttpResponse(simplejson.dumps(list(tags)),
                        mimetype='application/json')
