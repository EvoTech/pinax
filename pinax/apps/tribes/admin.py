from __future__ import absolute_import, unicode_literals
from django.contrib import admin

from pinax.apps.tribes.models import Tribe, TribeMember, TribeMemberHistory,\
    TribeRole, TribeMemberRole


class TribeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "creator", "created", ]
    raw_id_fields = ["creator", ]
    search_fields = ['slug', 'name', ]

admin.site.register(Tribe, TribeAdmin)


class TribeRoleAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "title", ]
    search_fields = ['name', 'title', 'description', ]

admin.site.register(TribeRole, TribeRoleAdmin)


class TribeMemberRoleAdmin(admin.ModelAdmin):
    list_display = ["id", "member", "role", "actor", "date", ]
    raw_id_fields = ["member", "role", "actor", ]

admin.site.register(TribeMemberRole, TribeMemberRoleAdmin)


class TribeMemberAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "tribe", "user", ]
    raw_id_fields = ["tribe", "user", ]
    list_editable = ["status", ]
    list_filter = ["status", ]

admin.site.register(TribeMember, TribeMemberAdmin)


class TribeMemberHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "member", "date", "actor", ]
    raw_id_fields = ["member", "actor", ]
    list_filter = ["status", ]
    search_fields = ['message', ]

admin.site.register(TribeMemberHistory, TribeMemberHistoryAdmin)
