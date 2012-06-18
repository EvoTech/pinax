from __future__ import absolute_import, unicode_literals
from django.conf.urls.defaults import *
from django.conf import settings
from pinax.apps.wiki.forms import WIKI_WORD_RE

WIKI_URL_RE = WIKI_WORD_RE

urlpatterns = patterns('pinax.apps.wiki.views',
    url(r'^$', 'article_list', name='wiki_index'),
    url(r'^list/$', 'article_list', name='wiki_list'),
    url(r'^search/$', 'search_article', name="wiki_search"),
    url(r'^history/$', 'history', name='wiki_history'),
    url(r'^feeds/(?P<feedtype>\w+)/$', 'history_feed', name='wiki_history_feed'),
    url(r'^(?P<title>' + WIKI_URL_RE + r')/feeds/(?P<feedtype>\w+)/$', 'article_history_feed',
        name='wiki_article_history_feed'),
    url(r'^(?P<title>' + WIKI_URL_RE + r')/$', 'view_article',
        name='wiki_article'),
    url(r'^edit/(?P<title>' + WIKI_URL_RE + r')/$', 'edit_article',
        name='wiki_edit'),
    url(r'^remove/(?P<title>' + WIKI_URL_RE + r')/$', 'remove_article',
        name='wiki_remove_article'),
    url(r'observe/(?P<title>' + WIKI_URL_RE + r')/$', 'observe_article',
        name='wiki_observe'),
    url(r'observe/(?P<title>' + WIKI_URL_RE + r')/stop/$', 'stop_observing_article',
        name='wiki_stop_observing'),
    url(r'^history/(?P<title>' + WIKI_URL_RE + r')/$', 'article_history',
        name='wiki_article_history'),
    url(r'^history/(?P<title>' + WIKI_URL_RE + r')/changeset/(?P<revision>\d+)/$', 'view_changeset',
        name='wiki_changeset',),
    url(r'^history/(?P<title>' + WIKI_URL_RE + r')/revert/$', 'revert_to_revision',
        name='wiki_revert_to_revision'),
)
