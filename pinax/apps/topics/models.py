from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from tagging.fields import TagField
from threadedcomments.models import ThreadedComment

MARKUP_CHOICES = getattr(settings, "MARKUP_CHOICES", [])


class Topic(models.Model):
    """
    a discussion topic for the tribe.
    """
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey("content_type", "object_id")
    
    title = models.CharField(_("title"), max_length=255, db_index=True)
    creator = models.ForeignKey(User,
        related_name = "created_topics",
        verbose_name = _("creator")
    )
    created = models.DateTimeField(_("created"), default=datetime.now, db_index=True)
    modified = models.DateTimeField(_("modified"), default=datetime.now, db_index=True) # topic modified when commented on
    body = models.TextField(_("body"), blank=True)
    markup = models.CharField(_(u"Content Markup"),
        max_length=50,
        choices=MARKUP_CHOICES,
        null=True,
        blank=True
    )
    
    tags = TagField()
    
    class Meta:
        ordering = ["-modified"]
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        kwargs = {"topic_id": self.pk}

        if self.group:
            return self.group.content_bridge.reverse("topic_detail", self.group, kwargs=kwargs)
        else:
            return reverse("topic_detail", kwargs=kwargs)


def new_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Topic):
        topic = instance.content_object
        topic.modified = datetime.now()
        topic.save()
        if notification:
            # @@@ how do I know which notification type to send?
            # @@@ notification.send([topic.creator], "tribes_topic_response", {"user": instance.user, "topic": topic})
            #pass
            group = topic.group
            if group:
                notify_list = group.member_queryset().exclude(id__exact=instance.user.id) # @@@
            else:
                notify_list = User.objects.all().exclude(id__exact=instance.user.id)
            
            notification.send(notify_list, "topic_comment", {
                "user": instance.user, "topic": topic, "comment": instance, "group": group,
            })
models.signals.post_save.connect(new_comment, sender=ThreadedComment)
