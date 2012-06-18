from __future__ import absolute_import, unicode_literals
from django.db.models import signals, get_app
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_noop as _

try:
    notification = get_app('notification')
    
    # @@@ when implemented need to add back "in a project you're a member of" or similar
    
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("photos_image_comment", _("Image Comment"), _("a new comment has been made on a image"), default=2)
        notification.create_notice_type("photos_image_new", _("New image"), _("a new image been created"), default=1)
        
    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImproperlyConfigured:
    print("Skipping creation of NoticeTypes as notification app not found")
