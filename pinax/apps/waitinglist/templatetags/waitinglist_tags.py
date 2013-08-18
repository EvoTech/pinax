from __future__ import absolute_import, unicode_literals
from django import template

from pinax.apps.waitinglist.forms import WaitingListEntryForm



register = template.Library()



class WaitingListEntryFormNode(template.Node):
    
    def __init__(self, as_varname):
        self.as_varname = as_varname
    
    def get_form(self, context):
        return WaitingListEntryForm()
    
    def render(self, context):
        context[self.as_varname] = self.get_form(context)
        return ""


@register.tag
def waitinglist_entry_form(parser, token):
    """
    Get a (new) form object to post a new comment.
    
    Syntax::
    
        {% waitinglist_entry_form as [varname] %}
    
    """
    bits = token.split_contents()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'{0}' takes one 'as' argument".format(bits[0]))
    return WaitingListEntryFormNode(bits[2])
