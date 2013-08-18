from __future__ import absolute_import, unicode_literals
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def urchin():
    urchin_id = getattr(settings, "URCHIN_ID", None)
    if urchin_id:
        return """
    <script src="http://www.google-analytics.com/urchin.js" type="text/javascript"></script>
    <script type="text/javascript">
        _uacct = "{0}";
        urchinTracker();
    </script>
    """.format(settings.URCHIN_ID)
    else:
        return ""


@register.simple_tag
def ga():
    # Use new Google Analytics tracking code
    if not settings.DEBUG: # not to render GA tracking code if debug is True
        urchin_id = getattr(settings, "URCHIN_ID", None)
        if urchin_id:
            return """
    <script type="text/javascript">
        var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
        document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
    </script>
    <script type="text/javascript">
        var pageTracker = _gat._getTracker("{0}");
        pageTracker._trackPageview();
    </script>
        """.format(settings.URCHIN_ID)
    else:
        return ""
