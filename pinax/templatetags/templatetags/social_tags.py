from __future__ import absolute_import, unicode_literals
from django import template

register = template.Library()


@register.inclusion_tag('social/share.html', takes_context=True)
def share(context):
    return context
