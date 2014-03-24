from __future__ import absolute_import, unicode_literals
from datetime import datetime

from django.conf import settings
from django.core import urlresolvers
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from groups.base import Group
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

CROP_ANCHOR_CHOICES = (
    ('top', _('Top')),
    ('right', _('Right')),
    ('bottom', _('Bottom')),
    ('left', _('Left')),
    ('center', _('Center (Default)')),
)

PUBLISH_CHOICES = (
    (1, _("Public")),
    (2, _("Private")),
)


class PhotoSet(models.Model):
    """
    A set of photos
    """

    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"))
    publish_type = models.IntegerField(
        _("publish_type"),
        choices=PUBLISH_CHOICES,
        default=1
    )
    tags = TagField()

    class Meta:
        verbose_name = _("photo set")
        verbose_name_plural = _("photo sets")

    def __str__(self):
        return self.name


class Image(models.Model):
    """
    A photo with its details
    """
    image = models.ImageField(_('image'), max_length=100,
                              upload_to="photologue/photos", blank=True)
    date_taken = models.DateTimeField(_('date taken'), null=True, blank=True, editable=False)
    view_count = models.PositiveIntegerField(default=0, editable=False)
    crop_from = models.CharField(_('crop from'), blank=True, max_length=10, default='center', choices=CROP_ANCHOR_CHOICES)
    # effect = models.ForeignKey('PhotoEffect', null=True, blank=True, related_name="%(class)s_related", verbose_name=_('effect'))

    SAFETY_LEVEL = (
        (1, _("Safe")),
        (2, _("Not Safe")),
    )
    title = models.CharField(_("title"), max_length=200)
    title_slug = models.SlugField(_("slug"))
    caption = models.TextField(_("caption"), blank=True)
    date_added = models.DateTimeField(
        _("date added"),
        default=datetime.now,
        editable=False
    )
    is_public = models.BooleanField(
        _("is public"),
        default=True,
        help_text=_("Public photographs will be displayed in the default views.")
    )
    member = models.ForeignKey(
        User,
        related_name="added_photos",
        blank=True,
        null=True
    )
    safetylevel = models.IntegerField(
        _("safetylevel"),
        choices=SAFETY_LEVEL,
        default=1
    )
    photoset = models.ManyToManyField(
        PhotoSet,
        blank=True,
        verbose_name=_("photo set")
    )
    tags = TagField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.group:
            group = self.pool_set.all()[0].content_object
            return group.content_bridge.reverse(
                'photo_details', group,
                kwargs={'id': self.pk, }
            )
        return urlresolvers.reverse("photo_details", args=[self.pk])

    @property
    def group(self):
        """Returns group"""
        for pool in self.pool_set.all():
            group = pool.content_object
            if isinstance(group, Group):
                return group
        return None

    def is_allowed(self, user, perm=None):
        """Checks permissions."""
        if self.group:
            if perm in ('photos.view_image',
                        'photos.browse_image', ):
                return user.has_perm('view', self.group)

            if perm in ('photos.change_image', ):
                return self.member == user or user.has_perm(perm, self.group)

            if perm in ('photos.add_image', ):
                return self.group.user_is_member(user)

            if perm in ('comments.add_comment', ):
                return self.group.user_is_member(user) or\
                    user.has_perm(perm, self.group) or\
                    user.has_perm('photos.comment_image', self.group)

            if perm in ('photos.delete_image',
                        'comments.change_comment',
                        'comments.delete_comment', ):
                return user.has_perm(perm, self.group)

        else:
            if perm in ('photos.view_image',
                        'photos.browse_image', ):
                return True

            if perm in ('photos.change_image', ):
                return self.member == user

            if perm in ('photos.add_image',
                        'comments.add_comment', ):
                return user.is_authenticated()

            if perm in ('photos.delete_image',
                        'comments.change_comment',
                        'comments.delete_comment', ):
                return False

        return False


def reduce_patched(self, *a, **kw):
    """Excludes curry"""
    r = list(super(Image, self).__reduce__(*a, **kw))
    for k, v in r[2].copy().items():
        if getattr(v, '__name__', None) == '_curried':
            del r[2][k]
    return tuple(r)

# setattr(Image, '__reduce__', reduce_patched)


class Pool(models.Model):
    """
    model for a photo to be applied to an object
    """

    photo = models.ForeignKey(Image)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    created_at = models.DateTimeField(_("created_at"), default=datetime.now)

    class Meta:
        # Enforce unique associations per object
        unique_together = [("photo", "content_type", "object_id")]
        verbose_name = _("pool")
        verbose_name_plural = _("pools")

    def __str__(self):
        return str(self.content_object)

def subscribe_creator(sender, instance, created, **kwargs):
    if notification and created and isinstance(instance, Image):
        signal = notice_type_label = "photos_image_comment"
        observer = instance.member
        if observer and not notification.is_observing(instance, observer, signal):
            notification.observe(instance, observer, notice_type_label, signal)


def object_comment(sender, instance, created, **kwargs):
    if isinstance(instance.content_object, Image):
        observed = instance.content_object
        signal = notice_type_label = "photos_image_comment"
        observer = user = instance.user

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
                    "image": observed,
                    "comment": instance,
                    "group": observed.group,
                }
            )

if notification is not None:
    models.signals.post_save.connect(subscribe_creator, sender=Image)
    models.signals.post_save.connect(object_comment, sender=ThreadedComment)

# Python 2.* compatible
try:
    unicode
except NameError:
    pass
else:
    for cls in (PhotoSet, Image, Pool, ):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
