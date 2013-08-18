from __future__ import absolute_import, unicode_literals
from django import template
from django.conf import settings



register = template.Library()



class SilkNode(template.Node):
    """
    node class for silk tag
    """
    
    def __init__(self, name, attrs):
        self.name = template.Variable(name)
        self.attrs = {}
        for attr in attrs:
            key, value = attr.split("=")
            self.attrs[key] = template.Variable(value)
    
    def render(self, context):
        """
        render the img tag with specified attributes
        """
        name = self.name.resolve(context)
        attrs = []
        for k, v in self.attrs.items():
            attrs.append('{0}="{1}"'.format(k, v.resolve(context)))
        if attrs:
            attrs = " {0}".format(" ".join(attrs))
        else:
            attrs = ""
        return """<img src="{0}pinax/img/silk/icons/{1}.png"{2} />""".format(
            settings.STATIC_URL,
            name,
            attrs,
        )


@register.tag
def silk(parser, token):
    """
    Template tag to render silk icons
    Usage::
    
        {{ silk "image_name" arg1="value1" arg2="value2" ... }}
    
    """
    bits = token.split_contents()
    return SilkNode(bits[1], bits[2:])
