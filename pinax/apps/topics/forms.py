from django import forms

from tagging.forms import TagField
from pinax.apps.tagging_utils.widgets import TagAutoCompleteInput
from pinax.apps.topics.models import Topic



class TopicForm(forms.ModelForm):

    tags = TagField(label="Tags", required=False,
                    widget = TagAutoCompleteInput(
                    app_label=Topic._meta.app_label,
                    model=Topic._meta.module_name))
    
    class Meta:
        model = Topic
        fields = ["title", "body", "tags"]
