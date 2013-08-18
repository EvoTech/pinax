from __future__ import absolute_import, unicode_literals
import django.dispatch


user_logged_in = django.dispatch.Signal(providing_args=["request", "user"])