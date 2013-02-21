from __future__ import absolute_import, unicode_literals
from django import template



register = template.Library()


@register.simple_tag
def fk_field(obj):
    if obj:
        return """<a href="{0}">{1}</a>""".format(obj.get_absolute_url(), obj)
    else:
        return ""


@register.simple_tag
def mail_field(value):
    if value:
        return """<a href="mailto:{0}">{1}</a>""".format(value, value)
    else:
        return ""
