from __future__ import absolute_import, unicode_literals
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.db import models
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

import fts
from django_markup.markup import formatter
from tagging.fields import TagField
from tagging.models import Tag
from threadedcomments.models import ThreadedComment

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

try:
    import fts_ext
except ImportError:
    fts_ext = fts

try:
    str = unicode  # Python 2.* compatible
except NameError:
    pass

MARKUP_CHOICES = getattr(settings, "MARKUP_CHOICES", [])


class Post(fts.SearchableModel):
    """A model which holds a single post."""

    STATUS_CHOICES = (
        (1, _("Draft")),
        (2, _("Public")),
    )

    title = models.CharField(
        _("title"),
        max_length=200
    )
    slug = models.SlugField(
        _("slug")
    )
    author = models.ForeignKey(
        User,
        related_name="added_posts"
    )
    creator_ip = models.IPAddressField(
        _("IP Address of the Post Creator"),
        blank=True,
        null=True
    )
    tease = models.TextField(
        _("tease"),
        blank=True
    )
    body = models.TextField(
        _("body")
    )
    status = models.IntegerField(
        _("status"),
        choices=STATUS_CHOICES,
        default=2
    )
    allow_comments = models.BooleanField(
        _("allow comments"),
        default=True
    )
    publish = models.DateTimeField(
        _("publish"),
        default=datetime.now
    )
    created_at = models.DateTimeField(
        _("created at"),
        default=datetime.now
    )
    updated_at = models.DateTimeField(
        _("updated at")
    )
    markup = models.CharField(
        _("Post Content Markup"),
        max_length=50,
        choices=formatter.choices(MARKUP_CHOICES),
        null=True,
        blank=True
    )
    translation_of = models.ForeignKey(
        'self',
        related_name='translations',
        blank=True,
        null=True,
    )
    language = models.CharField(
        blank=False,
        null=False,
        choices=settings.LANGUAGES,
        max_length=10,
        default=translation.get_language,
        db_index=True
    )
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True
    )
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        db_index=True
    )
    group = generic.GenericForeignKey('content_type', 'object_id')
    tags = TagField()

    objects = fts_ext.SearchManager(fields=('title', 'tease', 'body'))

    class Meta:
        verbose_name = _("post")
        verbose_name_plural = _("posts")
        ordering = ["-publish"]
        get_latest_by = "publish"

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        self.updated_at = datetime.now()
        super(Post, self).save(**kwargs)

    def get_absolute_url(self):
        with translation.override(self.language):
            return urlresolvers.reverse("blog_post", kwargs={
                "username": self.author.username,
                "year": self.publish.year,
                "month": "{0:02d}".format(self.publish.month),
                "slug": self.slug
            })

    def is_allowed(self, user, perm=None):
        """Checks permissions."""
        if perm in ('blog.view_post',
                    'blog.browse_post'):
            return self.status == 2 or self.author == user

        if perm in ('blog.add_post',
                    'comments.add_comment', ):
            return user.is_authenticated()

        if perm in ('blog.change_post', ):
            return self.author == user

        if perm in ('blog.delete_post',
                    'comments.change_comment',
                    'comments.delete_comment', ):
            return False

        return False


def subscribe_creator(sender, instance, created, **kwargs):
    if notification and created and isinstance(instance, Post):
        signal = notice_type_label = "blog_post_comment"
        observer = instance.author
        if observer and not notification.is_observing(instance, observer, signal):
            notification.observe(instance, observer, notice_type_label, signal)


def object_comment(sender, instance, created, **kwargs):
    if isinstance(instance.content_object, Post):
        observed = instance.content_object
        signal = notice_type_label = "blog_post_comment"
        observer = user = instance.user
        # Post.objects.filter(pk=observed.pk).update(updated_at=datetime.now())  # Don't send a signal

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
                    "notice_uid": notice_uid,
                    "user": user,
                    "post": observed,
                    "comment": instance
                }
            )

if notification is not None:
    models.signals.post_save.connect(subscribe_creator, sender=Post)
    models.signals.post_save.connect(object_comment, sender=ThreadedComment)

# Python 2.* compatible
try:
    unicode
except NameError:
    pass
else:
    for cls in (Post, ):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
