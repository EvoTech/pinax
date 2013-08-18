from __future__ import absolute_import, unicode_literals
import math
from django import template
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from classytags.core import Tag, Options
from classytags.arguments import Argument

register = template.Library()

class Ads(Tag):
    name = 'ads'
    options = Options(
        Argument('name', required=True),
        'as',
        Argument('varname', required=False, resolve=True)
    )
    
    def render_tag(self, context, name, varname):
        out = ''
        languages = [context['LANGUAGE_CODE'],
                     context['LANGUAGE_CODE'].split('-')[0],
                     'default']
        #if languages[1] == 'uk':
        #    languages.insert(2, 'ru')
        for l in languages:
            try:
                out = render_to_string('ads/{0}/{1}.html'.format(l, name), context)
                out = mark_safe("""<div class="ads">{0}</div>""".format(out))
                break
            except:
                pass
        show = getattr(settings, 'ADS_SHOW', False)
        if not show:
            out = ''
        if varname:
            context[varname] = out
            return ''
        return out

register.tag(Ads)


@register.filter
def in_list_ads(current, total):
    if isinstance(total, (models.Model, list, tuple)):
        total=len(total)
    if not isinstance(total, (int, float)):
        total = int(total)
    
    if current == math.floor(total/3.8):
        return True
    return False

