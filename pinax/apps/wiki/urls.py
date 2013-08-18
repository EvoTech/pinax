from __future__ import absolute_import, unicode_literals
from django.conf.urls.defaults import *
from django.conf import settings
from pinax.apps.wiki.forms import WIKI_WORD_RE

WIKI_URL_RE = WIKI_WORD_RE

urlpatterns = patterns('pinax.apps.wiki.views',
    url(r'^$', 'article_list', name='wiki_index'),
    url(r'^list/$', 'article_list', name='wiki_list'),
    url(r'^search/$', 'search_article', name="wiki_search"),
    url(r'^(?P<title>' + WIKI_URL_RE + r')/$', 'view_article',
        name='wiki_article'),
    url(r'^edit/(?P<title>' + WIKI_URL_RE + r')/$', 'edit_article',
        name='wiki_edit'),
    url(r'^remove/(?P<title>' + WIKI_URL_RE + r')/$', 'remove_article',
        name='wiki_remove_article'),
)
