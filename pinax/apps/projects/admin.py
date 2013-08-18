from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from pinax.apps.projects.models import Project



class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "creator", "created"]



admin.site.register(Project, ProjectAdmin)