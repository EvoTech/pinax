from __future__ import absolute_import, unicode_literals
from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r"^login/$", "pinax.apps.authsub.views.login", name="authsub_login"),
)
