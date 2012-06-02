from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from photologue.models import *

from tagging.fields import TagField

from django.utils.translation import ugettext_lazy as _



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
        return reverse("photo_details", args=[self.pk])

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

            if perm in ('photos.observe_image_new_image',
                        'photos.observe_image_comment_image', ):
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

            if perm in ('photos.observe_image_new_image',
                        'photos.observe_image_comment_image', ):
                return user.is_authenticated()

        return False


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
