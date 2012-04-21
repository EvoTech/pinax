from django.contrib import admin

from pinax.apps.tribes.models import Tribe, TribeMember


class TribeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "creator", "created", ]
    raw_id_fields = ["creator", ]
    search_fields = ['slug', 'name', ]

admin.site.register(Tribe, TribeAdmin)


class TribeMemberAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "tribe", "user", ]
    raw_id_fields = ["tribe", "user", ]
    list_editable = ["status", ]
    list_filter = ["status", ]

admin.site.register(TribeMember, TribeMemberAdmin)
