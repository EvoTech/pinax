# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re
import sys

from django import forms
from django.forms import widgets
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from tagging.forms import TagField
from pinax.apps.tagging_utils.widgets import TagAutoCompleteInput
from markup_form.forms import make_maprkup_form
from pinax.apps.wiki.models import Article

#DEFAULT_WIKI_WORD_RE = ur"(?:[A-Z]+[a-z0-9']+){2,}"
#DEFAULT_WIKI_WORD_RE = ur"((([A-Z]+[a-z0-9']+){2,})(/([A-Z]+[a-z0-9']+){2,})*)"

uppers = []
lowers = []

for i in range(sys.maxunicode):
  c = unichr(i)
  if c.isupper():
    uppers.append(c)
  elif c.islower():
    lowers.append(c)

uppers = r"".join(uppers)
lowers = r"".join(lowers)

DEFAULT_WIKI_WORD_RE = r"((([" + uppers + r"]+[" + lowers + r"0-9']+){2,})(/([" + uppers + r"]+[" + lowers + r"0-9']+){2,})*)"

WIKI_WORD_RE = getattr(settings, 'WIKI_WORD_RE', DEFAULT_WIKI_WORD_RE)

wikiword_pattern = re.compile(r'^' + WIKI_WORD_RE + r'$', re.U)

try:
    WIKI_BANNED_TITLES = settings.WIKI_BANNED_TITLES
except AttributeError:
    WIKI_BANNED_TITLES = ('NewArticle', 'EditArticle',)


class ArticleFormBase(forms.ModelForm):

    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '20'}))

    summary = forms.CharField(
        required=False, max_length=255,
        widget=forms.Textarea(attrs={'rows': '5'}))

    tags = TagField(label="Tags", required=False,
                    widget = TagAutoCompleteInput(
                    app_label=Article._meta.app_label,
                    model=Article._meta.module_name))

    comment = forms.CharField(required=False, max_length=50)
    user_ip = forms.CharField(widget=forms.HiddenInput)

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        required=False,
        widget=forms.HiddenInput)
    object_id = forms.IntegerField(required=False,
                                   widget=forms.HiddenInput)

    action = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Article
        exclude = ('creator', 'creator_ip', 'removed',
                   'group', 'created_at', 'last_update')

    def clean_title(self):
        """ Page title must be a WikiWord.
        """
        title = self.cleaned_data['title']
        if title in WIKI_BANNED_TITLES:
            raise forms.ValidationError(_('Invalid page title.'))
        if not wikiword_pattern.match(title):
            raise forms.ValidationError(_('Must be a WikiWord.'))

        return title

    def clean(self):
        super(ArticleFormBase, self).clean()
        kw = {}

        if self.cleaned_data['action'] == 'create':
            try:
                kw['title'] = self.cleaned_data['title']
                kw['content_type'] = self.cleaned_data['content_type']
                kw['object_id'] = self.cleaned_data['object_id']
            except KeyError:
                pass # some error in this fields
            else:
                if Article.objects.filter(**kw).count():
                    raise forms.ValidationError(
                        _("An article with this title already exists."))

        return self.cleaned_data

    def save(self):
        self.instance.revision_info = {
            'comment': self.cleaned_data['comment'],
            'editor_ip': self.cleaned_data['user_ip'],
            'editor': getattr(self, 'editor', None),
        }
        # 0 - Extra data
        editor_ip = self.cleaned_data['user_ip']
        comment = self.cleaned_data['comment']

        # 1 - Get the old stuff before saving
        if self.instance.id is None:
            old_title = old_content = old_markup = ''
            new = True
        else:
            old = Article.objects.get(pk=self.instance.pk)
            old_title = old.title
            old_content = old.content
            old_markup = old.markup
            new = False

        # 2 - Save the Article
        article = super(ArticleFormBase, self).save()

        # 3 - Set creator and group
        editor = getattr(self, 'editor', None)
        group = getattr(self, 'group', None)
        if new:
            article.creator_ip = editor_ip
            if editor is not None:
                article.creator = editor
                article.group = group
            article.save()

        # 4 - Create new revision
        changeset = article.new_revision(
            old_content, old_title, old_markup,
            comment, editor_ip, editor)

        return article, changeset


class SearchForm(forms.Form):
    q = forms.CharField(required=True, label=_('Search'))
    title_only = forms.BooleanField(required=False, label=_('Title only?'))

ArticleForm = make_maprkup_form(
    ArticleFormBase,
    {'markup': ['content', 'summary', ], }
)
