from django.conf.urls import patterns, url

urlpatterns = patterns('pinax.apps.threadedcomments_extras.views',
    url(r'^delete/(\d+)/$',  'delete',           name='comments-delete'),
    url(r'^deleted/$',       'delete_done',      name='comments-delete-done'),
)
