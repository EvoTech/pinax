from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from pinax.apps.wiki.models import Article


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'markup', 'created_at', 'last_update', 'removed',
                    'content_type', 'object_id', 'group', )
    list_filter = ('content_type', 'removed', )
    list_editable = ('removed', )
    search_fields = ('title', 'summary', 'content', )
    ordering = ('last_update', )
    raw_id_fields = ('creator', )
    fieldsets = (
        (None, {'fields': ('title', 'content', 'markup')}),
        ('Creator', {'fields': ('creator', 'creator_ip'),
                     'classes': ('collapse', 'wide')}),
        ('Group', {'fields': ('object_id', 'content_type'),
                     'classes': ('collapse', 'wide')}),
    )

admin.site.register(Article, ArticleAdmin)
