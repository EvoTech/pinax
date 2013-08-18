from __future__ import absolute_import, unicode_literals
from django import template
from django.template.defaultfilters import stringfilter

from django_markup_ext.utils.oembed_ext import replace, replace_bs, clearfix

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def oembed_ext(text, args=None):
    """More intelligent oembed filter"""
    if args:
        try:
            width, height = list(map(int, args.lower().split('x')))
        except ValueError:
            raise template.TemplateSyntaxError("Oembed's optional " \
                "WIDTHxHEIGHT argument requires WIDTH and HEIGHT to be " \
                "positive integers.")
    else:
        width, height = None, None

    return replace_bs(text, max_width=width, max_height=height)


@register.filter(is_safe=True)
@stringfilter
def oembed_clearfix(string):
    """Removed wrapped tags.

    For example, if oembed filter applied after urlize.
    Like this: <a href="<iframe...></iframe>">...</a>
    """
    return clearfix(string)
