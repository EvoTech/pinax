from pinax.apps.blog.models import Post
from django.contrib import admin



class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "publish", "status"]
    list_filter = ["publish", "status"]
    search_fields = ["title", "body", "tease"]
    prepopulated_fields = {"slug": ["title"]}
    raw_id_fields = ["author", ]



admin.site.register(Post, PostAdmin)
