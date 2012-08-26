from __future__ import absolute_import, unicode_literals
from django.conf.urls.defaults import *


urlpatterns = patterns("",
    url(r'^account/', include('pinax.apps.account.urls')),
)
