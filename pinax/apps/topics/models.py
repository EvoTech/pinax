from __future__ import absolute_import, unicode_literals
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_markup.markup import formatter
from tagging.fields import TagField
from threadedcomments.models import ThreadedComment

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

try:
    str = unicode  # Python 2.* compatible
except NameError:
    pass

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
    markup = models.CharField(_("Content Markup"),
        max_length=50,
        choices=formatter.choices(MARKUP_CHOICES),
        null=True,
        blank=True
    )
    
    tags = TagField()
    
    class Meta:
        ordering = ["-modified"]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        kwargs = {"topic_id": self.pk}

        if self.group:
            return self.group.content_bridge.reverse("topic_detail", self.group, kwargs=kwargs)
        else:
            return urlresolvers.reverse("topic_detail", kwargs=kwargs)

    def is_allowed(self, user, perm=None):
        """Checks permissions."""
        if self.group:
            if perm in ('topics.view_topic',
                        'topics.browse_topic', ):
                return user.has_perm('view', self.group)

            if perm in ('topics.change_topic', ):
                return self.creator == user or user.has_perm(perm, self.group)

            if perm in ('topics.add_topic', ):
                return self.group.user_is_member(user)

            if perm in ('comments.add_comment', ):
                return self.group.user_is_member(user) or\
                    user.has_perm(perm, self.group) or\
                    user.has_perm('topics.comment_topic', self.group)

            if perm in ('topics.delete_topic',
                        'comments.change_comment', 
                        'comments.delete_comment', ):
                return user.has_perm(perm, self.group)

        else:
            if perm in ('topics.view_topic',
                        'topics.browse_topic', ):
                return True

            if perm in ('topics.change_topic', ):
                return self.creator == user

            if perm in ('topics.add_topic',
                        'comments.add_comment', ):
                return user.is_authenticated()

            if perm in ('topics.delete_topic',
                        'comments.change_comment', 
                        'comments.delete_comment', ):
                return False

        return False


def topic_new(sender, instance, **kwargs):
    if isinstance(instance, Topic):
        topic = instance
        if notification and kwargs.get('created'):
            group = topic.group
            if group:
                notify_list = group.member_queryset().exclude(id__exact=instance.creator.id) # @@@
            else:
                notify_list = User.objects.all().exclude(id__exact=instance.creator.id)
            
            notification.send(notify_list, "topic_new", {
                "creator": instance.creator,
                "topic": topic,
                "group": group,
                "context_object": topic,
            })


def subscribe_creator(sender, instance, created, **kwargs):
    if notification and created and isinstance(instance, Topic):
        signal = notice_type_label = 'topic_comment'
        observer = instance.creator
        if observer and not notification.is_observing(instance, observer, signal):
            notification.observe(instance, observer, notice_type_label, signal)


def object_comment(sender, instance, created, **kwargs):
    if isinstance(instance.content_object, Topic):
        observed = instance.content_object
        signal = notice_type_label = 'topic_comment'
        observer = user = instance.user
        Topic.objects.filter(pk=observed.pk).update(modified=datetime.now())  # Don't send a signal

        if notification and created:

            if not notification.is_observing(observed, observer, signal):
                notification.observe(observed, observer, notice_type_label, signal)

            notice_uid = '{0}_{1}_{2}'.format(
                notice_type_label,
                Site.objects.get_current().pk,
                instance.pk
            )

            notification.send_observation_notices_for(
                observed, signal, extra_context={
                    "context_object": instance,
                    "user": user,
                    "topic": observed,
                    "comment": instance,
                    "group": observed.group,
                    "notice_uid": notice_uid,
                }
            )

if notification is not None:
    models.signals.post_save.connect(topic_new, sender=Topic)
    models.signals.post_save.connect(subscribe_creator, sender=Topic)
    models.signals.post_save.connect(object_comment, sender=ThreadedComment)

# Python 2.* compatible
try:
    unicode
except NameError:
    pass
else:
    for cls in (Topic, ):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
