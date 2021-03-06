from __future__ import absolute_import, unicode_literals
from django.conf.urls.defaults import *

from pinax.apps.blog import views, models
from pinax.apps.blog.forms import *



urlpatterns = patterns("",
    # blog post
    url(r"^post/(?P<username>[\w.+_-]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<slug>[\w.+_-]+)/$", "pinax.apps.blog.views.post", name="blog_post"),
    
    # all blog posts
    url(r"^$", "pinax.apps.blog.views.blogs", name="blog_list_all"),
    
    # blog post for user
    url(r"^posts/(?P<username>[\w.+_-]+)/$", "pinax.apps.blog.views.blogs", name="blog_list_user"),
    
    # your posts
    url(r"^your_posts/$", "pinax.apps.blog.views.your_posts", name="blog_list_yours"),
    
    # new blog post
    url(r"^new/$", "pinax.apps.blog.views.new", name="blog_new"),
    
    # edit blog post
    url(r"^edit/(\d+)/$", "pinax.apps.blog.views.edit", name="blog_edit"),
    
    #destory blog post
    url(r"^destroy/(\d+)/$", "pinax.apps.blog.views.destroy", name="blog_destroy"),
)
