from __future__ import absolute_import, unicode_literals
from pinax.apps.blog.models import Post
from django.contrib import admin



class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "publish", "status", "author"]
    list_filter = ["publish", "status", "language"]
    search_fields = ["title", "body", "tease", "slug"]
    prepopulated_fields = {"slug": ["title"]}
    raw_id_fields = ["author", ]



admin.site.register(Post, PostAdmin)
