from django.contrib import admin
from django.template.defaultfilters import truncatewords_html

from threadedcomments.admin import ThreadedCommentsAdmin as ThreadedCommentsAdminOrigin
from threadedcomments.models import ThreadedComment


class ThreadedCommentsAdmin(ThreadedCommentsAdminOrigin):

    list_display = ('id', 'title', 'introduction', 'content_type', 'object_pk',
                    'content_object', 'parent', 'name', 'user', 'ip_address',
                    'submit_date', 'is_public', 'is_removed', )
    raw_id_fields = ("parent", 'user', )
    list_filter = ('submit_date', 'site', 'is_public',
                   'is_removed', 'content_type', )

    def introduction(self, obj):
        """Short introduction"""
        return truncatewords_html(obj.comment, 12)

admin.site.unregister(ThreadedComment)
admin.site.register(ThreadedComment, ThreadedCommentsAdmin)
