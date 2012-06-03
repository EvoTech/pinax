from datetime import datetime

from django.core import urlresolvers
from django.db import models

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from groups.base import Group
from tagging.fields import TagField
from threadedcomments.models import ThreadedComment

from photologue.models import *

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

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
    publish_type = models.IntegerField(_("publish_type"),
        choices = PUBLISH_CHOICES,
        default = 1
    )
    tags = TagField()
    
    class Meta:
        verbose_name = _("photo set")
        verbose_name_plural = _("photo sets")


class Image(ImageModel):
    """
    A photo with its details
    """
    
    SAFETY_LEVEL = (
        (1, _("Safe")),
        (2, _("Not Safe")),
    )
    title = models.CharField(_("title"), max_length=200)
    title_slug = models.SlugField(_("slug"))
    caption = models.TextField(_("caption"), blank=True)
    date_added = models.DateTimeField(_("date added"),
        default = datetime.now,
        editable = False
    )
    is_public = models.BooleanField(_("is public"),
        default = True,
        help_text = _("Public photographs will be displayed in the default views.")
    )
    member = models.ForeignKey(User,
        related_name = "added_photos",
        blank = True,
        null = True
    )
    safetylevel = models.IntegerField(_("safetylevel"),
        choices = SAFETY_LEVEL,
        default = 1
    )
    photoset = models.ManyToManyField(PhotoSet,
        blank = True,
        verbose_name = _("photo set")
    )
    tags = TagField()
    
    def __unicode__(self):
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
            if isinstance(group, (Group, )):
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

            if perm in ('photos.observe_photos_image_new_image',
                        'photos.observe_photos_image_comment_image', ):
                return self.group.user_is_member(user)

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

            if perm in ('photos.observe_photos_image_new_image',
                        'photos.observe_photos_image_comment_image', ):
                return user.is_authenticated()

        return False


def reduce_patched(self, *a, **kw):
    """Excludes curry"""
    r = list(super(ImageModel, self).__reduce__(*a, **kw))
    for k, v in r[2].copy().iteritems():
        if getattr(v, '__name__', None) == '_curried':
            del r[2][k]
    return tuple(r)

setattr(ImageModel, '__reduce__', reduce_patched)


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


def photos_image_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Image):
        image = instance.content_object
        if notification:
            group = image.group
            notify_list = [image.member.pk, ]
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            notify_list += ThreadedComment.objects.for_model(image).filter(
                is_public=True,
                is_removed=False,
                site=current_site,
                object_pk=image.pk
            ).values_list('user', flat=True)
            notify_list = list(set(notify_list))
            if instance.user.pk in notify_list:
                notify_list.remove(instance.user.pk)
            notification.send(notify_list, "photos_image_comment", {
                "user": instance.user,
                "image": image,
                "comment": instance,
                "group": group,
            })

models.signals.post_save.connect(photos_image_comment, sender=ThreadedComment)
