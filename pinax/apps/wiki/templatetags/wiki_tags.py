import re

from django import template
from django.core.urlresolvers import reverse
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.functional import curry
from django.utils.safestring import mark_safe, SafeData

from pinax.apps.wiki.forms import WIKI_WORD_RE


register = template.Library()

# wikiword_link = re.compile(r'(?<!!)\b((?:\.?\./)*{0})\b'.format(WIKI_WORD_RE), re.U)
wikiword_link = re.compile(r'(\!?(?:\.?\./)*\b{0})\b'.format(WIKI_WORD_RE), re.U)


def _re_callback(match, inside=False, group=None):
    """Regexp callback"""
    title = match.group(1)
    # escaped
    if title[0] == '!':
        return title[1:]
    # relative, keep as is
    if title[0] in ('.', '/'):
        url = title
    else:
        if group:
            bridge = group.content_bridge
            url = bridge.reverse('wiki_article', group, kwargs={'title': title, })
        else:
            url = reverse('wiki_article', kwargs={'title': title, })
    if inside:
        return url
    return u"""<a href="{0}">{1}</a>""".format(url, title)


@register.filter
@stringfilter
def wiki_links(text, group=None):
    """More intelligent oembed replacer, bsaed on BeautifulSoup."""
    from BeautifulSoup import BeautifulSoup

    autoescape=False
    safe_input = isinstance(text, SafeData)
    conditional_escape(text)
    soup = BeautifulSoup(text)

    for url in soup.findAll(text=wikiword_link):
        if url.parent.name == 'a':
            continue
        new_str = wikiword_link.sub(curry(_re_callback, inside=False, group=group), unicode(url))
        url.replaceWith(new_str)

    for a in soup.findAll('a'):
        url = a['href']
        new_str = wikiword_link.sub(curry(_re_callback, inside=True, group=group), unicode(url))
        if unicode(new_str) != url:
            a['href'] = new_str

    result = unicode(soup)
    if safe_input:
        result = mark_safe(result)
    elif autoescape:
        result = escape(result)
    return result


@register.inclusion_tag('wiki/article_teaser.html')
def show_teaser(article):
    """ Show a teaser box for the summary of the article.
    """
    return {'article': article}


@register.inclusion_tag('wiki/wiki_title.html')
def wiki_title(group):
    """ Display a <h1> title for the wiki, with a link to the group main page.
    """
    if group:
        return {'group': group,
                'group_name': group.name,
                'group_type': group._meta.verbose_name.title(),
                'group_url': group.get_absolute_url()}
    else:
        # no need to put group in context since it is None
        return {}
