from __future__ import absolute_import, unicode_literals
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.test import TestCase

from pinax.apps.tribes.models import Tribe, TribeMember


class TribesTest(TestCase):
    # fixtures = ["tribes_auth.json"]
    # urls = "pinax.apps.tribes.tests.tribes_urls"

    def setUp(self):
        self.user = User.objects.create_user(
            username='tester',
            email="tester@mailinator.com",
            password="tester"
        )

    def test_unauth_create_get(self):
        """
        can an unauth'd user get to page?
        """

        response = self.client.get(urlresolvers.reverse("tribe_create"))
        self.assertEqual(response.status_code, 302)
        #self.assertEqual(response["location"], "http://testserver/account/login/?next={0}".format(urlresolvers.reverse("tribe_create")))

    def test_auth_create_get(self):
        """
        can an auth'd user get to page?
        """

        logged_in = self.client.login(username="tester", password="tester")
        self.assertTrue(logged_in)
        response = self.client.get(urlresolvers.reverse("tribe_create"))
        self.assertEqual(response.status_code, 200)

    def test_unauth_create_post(self):
        """
        can an unauth'd user post to create a new tribe?
        """

        response = self.client.post(urlresolvers.reverse("tribe_create"))
        self.assertEqual(response.status_code, 302)
        #self.assertEqual(response["location"], "http://testserver/account/login/?next={0}".format(urlresolvers.reverse("tribe_create")))

    def test_auth_create_post(self):
        """
        can an auth'd user post to create a new tribe?
        """

        logged_in = self.client.login(username="tester", password="tester")
        self.assertTrue(logged_in)
        response = self.client.post(urlresolvers.reverse("tribe_create"), {
            "slug": "test",
            "name": "Test Tribe",
            "description": "A test tribe.",
        })
        self.assertEqual(response.status_code, 302)
        #self.assertEqual(response["location"], "http://testserver/tribes/tribe/test/")
        self.assertEqual(Tribe.objects.get(slug="test").creator.username, "tester")
        self.assertEqual(Tribe.objects.get(slug="test").member_queryset().all()[0].username, "tester")

    def test_auth_creator_membership(self):
        """
        is membership for creator correct?
        """

        logged_in = self.client.login(username="tester", password="tester")
        self.assertTrue(logged_in)
        response = self.client.post(urlresolvers.reverse("tribe_create"), {
            "slug": "test",
            "name": "Test Tribe",
            "description": "A test tribe.",
        })
        response = self.client.get(urlresolvers.reverse("tribe_detail", args=["test"]))
        self.assertEqual(Tribe.objects.get(slug="test").creator.username, "tester")
        self.assertEqual(Tribe.objects.get(slug="test").member_queryset().all()[0].username, "tester")
        self.assertEqual(response.context[0]["is_member"], True)

    def test_members(self):
        creator = User.objects.create_user(
            username='creator',
            email="creator@mailinator.com",
            password="creator"
        )
        tribe = Tribe.objects.create(
            slug="test",
            name="Test Tribe",
            description="A test tribe.",
            private=True,
            creator=creator
        )


        response = self.client.get(urlresolvers.reverse('tribe_members', args=["test"]))
        self.assertEqual(response.status_code, 302)

        logged_in = self.client.login(username="tester", password="tester")
        self.assertTrue(logged_in)
        response = self.client.get(urlresolvers.reverse('tribe_members', args=["test"]))
        self.assertEqual(response.status_code, 403)

        TribeMember.objects.create(
            status='active',
            tribe=tribe,
            user=self.user
        )
        response = self.client.get(urlresolvers.reverse('tribe_members', args=["test"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tribe.name)
        self.assertContains(response, self.user.username)
