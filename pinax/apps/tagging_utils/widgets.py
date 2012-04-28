from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe



class TagAutoCompleteInput(forms.TextInput):
    
    def __init__(self, app_label, model, *args, **kwargs):
        self.app_label = app_label
        self.model = model
        super(TagAutoCompleteInput, self).__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None):
        output = super(TagAutoCompleteInput, self).render(name, value, attrs)
        
        return output + mark_safe(u"""<script type="text/javascript">
            jQuery("#id_{name}").autocomplete({{
                focus: function(){{
			// prevent value inserted on focus
			return false;
		}},
                source: function(request, response){{
			$.getJSON("{url}", {{
				term: request.term.split( /,\s*/ ).pop()
			}}, response);
		}},
                select: function(event, ui) {{
                    var terms = this.value.split( /,\s*/ );
                    // remove the current input
                    terms.pop();
                    // add the selected item
                    terms.push(ui.item.value);
                    // add placeholder to get the comma-and-space at the end
                    terms.push("");
                    this.value = terms.join(", ");
                    return false;
                }}
            }});
            </script>""".format(
                name=name,
                url=reverse("tagging_utils_autocomplete", kwargs={
                    "app_label": self.app_label,
                    "model": self.model
                })
            )
        )
