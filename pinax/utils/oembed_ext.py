import re
from django.utils.encoding import force_unicode
from django.utils.html import escape, smart_urlquote
from django.utils.safestring import SafeData, mark_safe

from oembed.core import replace as replace_orig

TRAILING_PUNCTUATION = ['.', ',', ':', ';']
WRAPPING_PUNCTUATION = [('(', ')'), ('<', '>'), ('&lt;', '&gt;')]
word_split_re = re.compile(r'(\s+)')
simple_url_re = re.compile(r'^https?://\w', re.IGNORECASE)
simple_url_2_re = re.compile(r'^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)$', re.IGNORECASE)

URL_PATTERN = '(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_|])'
URL_RE = re.compile(URL_PATTERN)


def replace_bs(text, max_width=None, max_height=None, autoescape=False):
    """More intelligent oembed replacer, bsaed on BeautifulSoup."""
    from BeautifulSoup import BeautifulSoup
    safe_input = isinstance(text, SafeData)
    soup = BeautifulSoup(text)
    for url in soup.findAll(text=re.compile(URL_RE)):
        if url.parent.name == 'a':
            continue
        new_str = replace_orig(unicode(url), max_width=max_width,
                               max_height=max_height)
        url.replaceWith(new_str)
    for a in soup.findAll('a'):
        url = u' {0} '.format(a['href'])
        new_str = replace_orig(url, max_width=max_width,
                               max_height=max_height)
        if unicode(new_str) != url:
            a.replaceWith(new_str)

    result = unicode(soup)
    if safe_input:
        result = mark_safe(result)
    elif autoescape:
        result = escape(result)
    return result


def replace(text, max_width=None, max_height=None, autoescape=False):
    """More intelligent oembed replacer"""

    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_unicode(text))
    for i, word in enumerate(words):
        if '.' in word or '@' in word or ':' in word:
            # Deal with punctuation.
            lead, middle, trail = '', word, ''
            for punctuation in TRAILING_PUNCTUATION:
                if middle.endswith(punctuation):
                    middle = middle[:-len(punctuation)]
                    trail = punctuation + trail
            for opening, closing in WRAPPING_PUNCTUATION:
                if middle.startswith(opening):
                    middle = middle[len(opening):]
                    lead = lead + opening
                # Keep parentheses at the end only if they're balanced.
                if (middle.endswith(closing)
                    and middle.count(closing) == middle.count(opening) + 1):
                    middle = middle[:-len(closing)]
                    trail = closing + trail

            # Make URL we want to point to.
            url = None
            if simple_url_re.match(middle):
                url = smart_urlquote(middle)
            elif simple_url_2_re.match(middle):
                url = smart_urlquote('http://%s' % middle)

            # Make link.
            if url:
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                middle = replace_orig(url, max_width=max_width,
                                      max_height=max_height)
                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return u''.join(words)


def clearfix(string):
    """Removed wrapped tags.

    For example, if oembed filter applied after urlize.
    Like this: <a href="<iframe...></iframe>">...</a>
    """
    string = force_unicode(string)
    A_RE = re.compile(
        u'<a[^>]*((?:<[^>]*>(?:[^<>]+<[^>]*>)*)+)[^>]*>.*</a>',
        re.UNICODE | re.IGNORECASE | re.S
    )
    IMG_RE = re.compile(
        u'<img[^>]*((?:<[^>]*>(?:[^<>]+<[^>]*>)*)+)[^>]*(?:/>|</img>)',
        re.UNICODE | re.IGNORECASE | re.S
    )
    string = A_RE.sub(u'\\1', string)
    string = IMG_RE.sub(u'\\1', string)
    return string
