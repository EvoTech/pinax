from datetime import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _

from tagging.forms import TagField
from markup_form.forms import make_maprkup_form
from pinax.apps.tagging_utils.widgets import TagAutoCompleteInput
from pinax.apps.blog.models import Post



class BlogFormBase(forms.ModelForm):
    
    slug = forms.SlugField(
        max_length = 20,
        help_text = _("a short version of the title consisting only of letters, numbers, underscores and hyphens."),
    )
    tags = TagField(label="Tags", required=False,
                    widget = TagAutoCompleteInput(
                        app_label=Post._meta.app_label,
                        model=Post._meta.module_name
                    ))

    class Meta:
        model = Post
        exclude = [
            "author",
            "creator_ip",
            "created_at",
            "updated_at",
            "publish",
        ]
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(BlogFormBase, self).__init__(*args, **kwargs)
    
    def clean_slug(self):
        if not self.instance.pk:
            if Post.objects.filter(author=self.user, created_at__month=datetime.now().month, created_at__year=datetime.now().year, slug=self.cleaned_data["slug"]).exists():
                raise forms.ValidationError(u"This field must be unique for username, year, and month")
            return self.cleaned_data["slug"]
        try:
            post = Post.objects.get(
                author = self.user,
                created_at__month = self.instance.created_at.month,
                created_at__year = self.instance.created_at.year,
                slug = self.cleaned_data["slug"]
            )
            if post != self.instance:
                raise forms.ValidationError(u"This field must be unique for username, year, and month")
        except Post.DoesNotExist:
            pass
        return self.cleaned_data["slug"]

BlogForm = make_maprkup_form(
    BlogFormBase,
    {'markup': ['body', 'tease', ], }
)
