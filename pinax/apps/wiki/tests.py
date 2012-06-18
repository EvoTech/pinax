# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.test import TestCase

from groups.base import Group
from groups.bridge import ContentBridge
from pinax.apps.wiki.templatetags.wiki_tags import wiki_links


class TestWikiGroup(Group):
    private = models.BooleanField(default=False)
    members = models.ManyToManyField(
        User,
        related_name="testwikigroups",
    )

    def get_absolute_url(self):
        return urlresolvers.reverse(
            "testwikigroup_detail",
            kwargs={"group_slug": self.slug}
        )

bridge = ContentBridge(TestWikiGroup)


def testwikigroup(request, group_slug=None):
    group = get_object_or_404(TestWikiGroup, slug=group_slug)
    html = "<html><body>Group {0}.</body></html>".format(group.name)
    return HttpResponse(html)

# Note, that settings.ROOT_URLCONF will be changed when WikiTest will be
# started. So, don't move urlpatterns to separate module, or import
# ROOT_URLCONF from tests file (before WikiTest will be started).
urlpatterns = patterns("",
    url(r'', include(settings.ROOT_URLCONF)),
    url(r"^testwikigroup/(?P<group_slug>[-\w]+)/$", testwikigroup,
        name="testwikigroup_detail"),
)
urlpatterns += bridge.include_urls(
    "pinax.apps.wiki.urls",
    r"^testwikigroup/(?P<testwikigroup_slug>[-\w]+)/wiki/"
)


class WikiTest(TestCase):

    urls = 'pinax.apps.wiki.tests'

    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            email="creator@mailinator.com",
            password="creatorpwd"
        )
        self.user = User.objects.create_user(
            username='test',
            email="test@mailinator.com",
            password="testpwd"
        )
        self.group = TestWikiGroup.objects.create(
            slug="test",
            name="Test Group",
            description="A test group.",
            creator=self.creator
        )

        self.group.members.add(self.user)
        self.assertTrue(self.group.user_is_member(self.user))

        response = self.client.login(username='test', password='testpwd')
        self.assertTrue(response)

    def test_wiki_links(self):
        self.assertEqual(
            wiki_links('слово ПримернаяСтраница слово', self.group),
            'слово <a href="/testwikigroup/test/wiki/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/">ПримернаяСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ./ПримернаяСтраница слово', self.group),
            'слово <a href="./%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">./ПримернаяСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ../ПримернаяСтраница слово', self.group),
            'слово <a href="../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">../ПримернаяСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ../../ПримернаяСтраница слово', self.group),
            'слово <a href="../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">../../ПримернаяСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ../../../ПримернаяСтраница слово', self.group),
            'слово <a href="../../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">../../../ПримернаяСтраница</a> слово'
        )

        self.assertEqual(
            wiki_links('слово !ПримернаяСтраница слово', self.group),
            'слово ПримернаяСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !./ПримернаяСтраница слово', self.group),
            'слово ./ПримернаяСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !../ПримернаяСтраница слово', self.group),
            'слово ../ПримернаяСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !../../ПримернаяСтраница слово', self.group),
            'слово ../../ПримернаяСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !../../../ПримернаяСтраница слово', self.group),
            'слово ../../../ПримернаяСтраница слово'
        )

        self.assertEqual(
            wiki_links('слово <a href="ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="/testwikigroup/test/wiki/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="./ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="./%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="../ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="../../ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="../../../ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="../../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )

        self.assertEqual(
            wiki_links('слово <a href="!ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="ПримернаяСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!./ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="./ПримернаяСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!../ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="../ПримернаяСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!../../ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="../../ПримернаяСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!../../../ПримернаяСтраница">текст</a> слово', self.group),
            'слово <a href="../../../ПримернаяСтраница">текст</a> слово'
        )

        self.assertEqual(
            wiki_links('слово ПримернаяСтраница/СубСтраница слово', self.group),
            'слово <a href="/testwikigroup/test/wiki/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/">ПримернаяСтраница/СубСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ./ПримернаяСтраница/СубСтраница слово', self.group),
            'слово <a href="./%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">./ПримернаяСтраница/СубСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ../ПримернаяСтраница/СубСтраница слово', self.group),
            'слово <a href="../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">../ПримернаяСтраница/СубСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ../../ПримернаяСтраница/СубСтраница слово', self.group),
            'слово <a href="../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">../../ПримернаяСтраница/СубСтраница</a> слово'
        )
        self.assertEqual(
            wiki_links('слово ../../../ПримернаяСтраница/СубСтраница слово', self.group),
            'слово <a href="../../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">../../../ПримернаяСтраница/СубСтраница</a> слово'
        )

        self.assertEqual(
            wiki_links('слово !ПримернаяСтраница/СубСтраница слово', self.group),
            'слово ПримернаяСтраница/СубСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !./ПримернаяСтраница/СубСтраница слово', self.group),
            'слово ./ПримернаяСтраница/СубСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !../ПримернаяСтраница/СубСтраница слово', self.group),
            'слово ../ПримернаяСтраница/СубСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !../../ПримернаяСтраница/СубСтраница слово', self.group),
            'слово ../../ПримернаяСтраница/СубСтраница слово'
        )
        self.assertEqual(
            wiki_links('слово !../../../ПримернаяСтраница/СубСтраница слово', self.group),
            'слово ../../../ПримернаяСтраница/СубСтраница слово'
        )

        self.assertEqual(
            wiki_links('слово <a href="ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="/testwikigroup/test/wiki/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="./ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="./%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="../ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="../../ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="../../../ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="../../../%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80%D0%BD%D0%B0%D1%8F%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0/%D0%A1%D1%83%D0%B1%D0%A1%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0">текст</a> слово'
        )

        self.assertEqual(
            wiki_links('слово <a href="!ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="ПримернаяСтраница/СубСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!./ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="./ПримернаяСтраница/СубСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!../ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="../ПримернаяСтраница/СубСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!../../ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="../../ПримернаяСтраница/СубСтраница">текст</a> слово'
        )
        self.assertEqual(
            wiki_links('слово <a href="!../../../ПримернаяСтраница/СубСтраница">текст</a> слово', self.group),
            'слово <a href="../../../ПримернаяСтраница/СубСтраница">текст</a> слово'
        )
