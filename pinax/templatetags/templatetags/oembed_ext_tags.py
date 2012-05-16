import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_unicode

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def oembed_clearfix(string):
    """Removed wrapped tags.

    For example, if oembed filter applied after urlize.
    Like this: <a href="<iframe...></iframe>">...</a>
    """
    string = force_unicode(string)
    A_RE = re.compile(
        u'<a[^>]*((?:<[^>]*>(?:[^<>]+<[^>]*>)*)+)[^>]*>.*</a>',
        re.UNICODE|re.IGNORECASE|re.S
    )
    IMG_RE = re.compile(
        u'<img[^>]*((?:<[^>]*>(?:[^<>]+<[^>]*>)*)+)[^>]*(?:/>|</img>)',
        re.UNICODE|re.IGNORECASE|re.S
    )
    string = A_RE.sub(u'\\1', string)
    string = IMG_RE.sub(u'\\1', string)
    return string
