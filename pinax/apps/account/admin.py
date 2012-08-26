from __future__ import absolute_import, unicode_literals
from django.contrib import admin

from pinax.apps.account.models import Account, OtherServiceInfo, PasswordReset



class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ["user", "temp_key", "timestamp", "reset"]



admin.site.register(Account)
admin.site.register(OtherServiceInfo)
admin.site.register(PasswordReset, PasswordResetAdmin)