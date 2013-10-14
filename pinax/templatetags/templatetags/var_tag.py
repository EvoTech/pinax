from __future__ import absolute_import, unicode_literals
from django import template



register = template.Library()



class VarNode(template.Node):
    
    def __init__(self, var_name, var_to_resolve):
        self.var_name = var_name
        self.var_to_resolve = var_to_resolve
    def get_context(self, top_context):
        for context in top_context.dicts:
            if self.var_name in context:
                return context
        return top_context
    def render(self, context):
        try:
            resolved_var = self.var_to_resolve.resolve(context)
            self.get_context(context)[self.var_name] = resolved_var
        except template.VariableDoesNotExist:
            self.get_context(context)[self.var_name] = ""
        return ""


@register.tag
def var(parser, token):
    """
    {% var foo = expression %}
    {% var foo = Model.foo_set.count %}
    {% var foo = foo|restructuredtext %}
    {{ foo }} {{ foo|escape }}
    """
    
    args = token.split_contents()
    if len(args) != 4 or args[2] != "=":
        raise template.TemplateSyntaxError(
            "'{0}' statement requires the form {{% {1} foo = bar %}}.".format(
                args[0], args[0])
            )
    return VarNode(args[1], parser.compile_filter(args[3]))
