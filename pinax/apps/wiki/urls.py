# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

from pinax.apps.wiki.forms import WIKI_WORD_RE

WIKI_URL_RE = WIKI_WORD_RE

urlpatterns = patterns('pinax.apps.wiki.views',
    url(ur'^$', 'article_list', name='wiki_index'),
    url(ur'^list/$', 'article_list', name='wiki_list'),
    url(ur'^search/$', 'search_article', name="wiki_search"),
    url(ur'^history/$', 'history', name='wiki_history'),
    url(ur'^feeds/(?P<feedtype>\w+)/$', 'history_feed', name='wiki_history_feed'),
    url(ur'^(?P<title>' + WIKI_URL_RE + ur')/feeds/(?P<feedtype>\w+)/$', 'article_history_feed',
        name='wiki_article_history_feed'),
    url(ur'^(?P<title>' + WIKI_URL_RE + ur')/$', 'view_article',
        name='wiki_article'),
    url(ur'^edit/(?P<title>' + WIKI_URL_RE + ur')/$', 'edit_article',
        name='wiki_edit'),
    url(ur'^remove/(?P<title>' + WIKI_URL_RE + ur')/$', 'remove_article',
        name='wiki_remove_article'),
    url(ur'observe/(?P<title>' + WIKI_URL_RE + ur')/$', 'observe_article',
        name='wiki_observe'),
    url(ur'observe/(?P<title>' + WIKI_URL_RE + ur')/stop/$', 'stop_observing_article',
        name='wiki_stop_observing'),
    url(ur'^history/(?P<title>' + WIKI_URL_RE + ur')/$', 'article_history',
        name='wiki_article_history'),
    url(ur'^history/(?P<title>' + WIKI_URL_RE + ur')/changeset/(?P<revision>\d+)/$', 'view_changeset',
        name='wiki_changeset',),
    url(ur'^history/(?P<title>' + WIKI_URL_RE + ur')/revert/$', 'revert_to_revision',
        name='wiki_revert_to_revision'),
)
