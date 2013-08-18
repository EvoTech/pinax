from __future__ import absolute_import, unicode_literals
from django import forms

from tagging.forms import TagField
from markup_form.forms import make_maprkup_form
from pinax.apps.tagging_utils.widgets import TagAutoCompleteInput
from pinax.apps.topics.models import Topic



class TopicFormBase(forms.ModelForm):

    tags = TagField(label="Tags", required=False,
                    widget=TagAutoCompleteInput(
                        app_label=Topic._meta.app_label,
                        model=Topic._meta.module_name
                    ))
    
    class Meta:
        model = Topic
        fields = ["title", "body", "markup", "tags", ]

TopicForm = make_maprkup_form(
    TopicFormBase,
    {'markup': ['body', ], }
)
