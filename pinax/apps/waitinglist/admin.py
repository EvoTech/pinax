from __future__ import absolute_import, unicode_literals
from django.contrib import admin

from pinax.apps.waitinglist.models import WaitingListEntry



class WaitingListEntryAdmin(admin.ModelAdmin):
    list_display = ["email", "created"]



admin.site.register(WaitingListEntry, WaitingListEntryAdmin)