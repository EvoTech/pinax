from __future__ import absolute_import, unicode_literals
from django.conf.urls.defaults import *



urlpatterns = patterns("",
    url(r"^login/$", "pinax.apps.bbauth.views.login", name="bbauth_login"),
    url(r"^success/$", "pinax.apps.bbauth.views.success", name="bbauth_success"),
    url(r"^logout/$", "pinax.apps.bbauth.views.logout", name="bbauth.logout"),
)