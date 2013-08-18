from __future__ import absolute_import, unicode_literals
import re
import copy
import posixpath
from django import template
from django.conf import settings

register = template.Library()

STRIP_NL_RE = re.compile(r'[\n\r\t ]+', re.S)


@register.inclusion_tag('social/share.html', takes_context=True)
def share(context, url=None, title='', description='', image=None):
    context = copy.copy(context)

    STATIC_URL = context.get('STATIC_URL', settings.STATIC_URL)

    if title and 'SITE_NAME' in context:
        title = '{0} - {1}'.format(title, context['SITE_NAME'])

    description = STRIP_NL_RE.sub(' ', description).strip()

    if not url:
        url = context['request'].build_absolute_uri()

    if not image:
        image = 'social/default_image.jpg'

    image = getattr(image, 'url', image)
    if not image.startswith('http'):
        if not image.startswith(STATIC_URL):
            image = posixpath.join(STATIC_URL, image)
        image = context['request'].build_absolute_uri(image)

    context.update({
        'url': url,
        'title': title,
        'description': description,
        'image': image,
    })
    return context
