from __future__ import absolute_import, unicode_literals
import sys
from django.conf import settings
from django.utils.html import escape, escapejs
from django.utils.functional import lazy, Promise, cached_property

try:
    str = unicode  # Python 2.* compatible
    string_types = (basestring,)
    integer_types = (int, long)
except NameError:
    string_types = (str,)
    integer_types = (int,)


def resolve(str_or_obj):
    """Returns object from string"""
    if not isinstance(str_or_obj, string_types):
        return str_or_obj
    if '.' not in str_or_obj:
        str_or_obj += '.'
    mod_name, obj_name = str_or_obj.rsplit('.', 1)
    __import__(mod_name)
    mod = sys.modules[mod_name]
    return getattr(mod, obj_name) if obj_name else mod


class Helper(Promise):
    """Help text"""

    def __init__(self, key, msg=None):
        self.msg = msg
        self.key = key

    @cached_property
    def callback(self):
        callback_default = lambda key: ""
        callback = getattr(
            settings,
            "HELPER_URL",
            callback_default
        )
        return resolve(callback)

    def get_url(self):
        return self.callback(self.key)

    def __str__(self):
        url = str(self.get_url())
        if not url:
            return ""

        onclick = escape("".format(
            url=escapejs(str(url))
        ))
        if "%(url)s" in self.msg:
            return str(self.msg % {'url': url, 'onclick': onclick})

        return """<a href="{url}" onclick="{onclick}" target="_blank">{msg}</a>""".format(
            msg=str(self.msg),
            url=url,
            onclick=onclick
        )

    __unicode__ = __str__


def helper(*args, **kwargs):
    """Just fabric"""
    return Helper(*args, **kwargs)
