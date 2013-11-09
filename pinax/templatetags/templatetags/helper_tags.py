from __future__ import absolute_import, unicode_literals

from django import template
from django.utils.html import mark_safe
from classytags.core import Tag, Options
from classytags.arguments import Argument
from pinax.utils.helper import helper

try:
    str = unicode  # Python 2.* compatible
    string_types = (basestring,)
    integer_types = (int, long)
except NameError:
    string_types = (str,)
    integer_types = (int,)

register = template.Library()


class HelperTag(Tag):
    name = 'helper'
    options = Options(
        Argument('key', required=True),
        Argument('msg', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )
    
    def render_tag(self, context, key, msg, varname):
        r = str(helper(key, msg))
        r = mark_safe(r)
        if varname:
            context[varname] = r
            return ''
        return r

register.tag(HelperTag)
