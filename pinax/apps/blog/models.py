from __future__ import absolute_import, unicode_literals
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_markup.markup import formatter
from tagging.fields import TagField
from tagging.models import Tag
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


class Post(models.Model):
    """
    A model which holds a single post.
    """
    
    STATUS_CHOICES = (
        (1, _("Draft")),
        (2, _("Public")),
    )
    
    title = models.CharField(_("title"), max_length=200)
    slug = models.SlugField(_("slug"))
    author = models.ForeignKey(User, related_name="added_posts")
    creator_ip = models.IPAddressField(_("IP Address of the Post Creator"),
        blank = True,
        null = True
    )
    body = models.TextField(_("body"))
    tease = models.TextField(_("tease"), blank=True)
    status = models.IntegerField(_("status"), choices=STATUS_CHOICES, default=2)
    allow_comments = models.BooleanField(_("allow comments"), default=True)
    publish = models.DateTimeField(_("publish"), default=datetime.now)
    created_at = models.DateTimeField(_("created at"), default=datetime.now)
    updated_at = models.DateTimeField(_("updated at"))
    markup = models.CharField(_("Post Content Markup"),
        max_length=50,
        choices=formatter.choices(MARKUP_CHOICES),
        null=True,
        blank=True
    )
    tags = TagField()
    
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


# handle notification of new comments
def new_comment(sender, instance, **kwargs):
    post = instance.content_object
    if isinstance(post, Post):
        if notification:
            notification.send([post.author], "blog_post_comment", {
                "user": instance.user,
                "post": post,
                "comment": instance
            })


models.signals.post_save.connect(new_comment, sender=ThreadedComment)

# Python 2.* compatible
try:
    unicode
except NameError:
    pass
else:
    for cls in (Post, ):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
