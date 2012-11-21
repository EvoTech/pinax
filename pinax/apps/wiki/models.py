from __future__ import absolute_import, unicode_literals
from django.core import urlresolvers

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.query import QuerySet

import versioning
from versioning.utils import revisions_for_object
from tagging.fields import TagField
from tagging.models import Tag
from threadedcomments.models import ThreadedComment

try:
    from notification import models as notification
    from django.db.models import signals
except ImportError:
    notification = None

try:
    str = unicode  # Python 2.* compatible
except NameError:
    pass

try:
    markup_choices = settings.WIKI_MARKUP_CHOICES
except AttributeError:
    markup_choices = (
        ('creole', _('Creole')),
        ('restructuredtext', _('reStructuredText')),
        ('textile', _('Textile')),
        ('markdown', _('Markdown')),
    )


# Avoid boilerplate defining our own querysets
class QuerySetManager(models.Manager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)


class NonRemovedArticleManager(QuerySetManager):
    def get_query_set(self):
        q = super(NonRemovedArticleManager, self).get_query_set()
        return q.filter(removed=False)


class Article(models.Model):
    """ A wiki page.
    """
    title = models.CharField(
        _("Title"),
        max_length=255,
        db_index=True
    )
    content = models.TextField(
        _("Content")
    )
    summary = models.CharField(
        _("Summary"),
        max_length=255,
        null=True,
        blank=True,
        db_index=True
    )
    markup = models.CharField(
        _("Content Markup"),
        max_length=100,
        choices=markup_choices,
        null=True,
        blank=True
    )
    creator = models.ForeignKey(
        User,
        verbose_name=_('Article Creator'),
        null=True
    )
    creator_ip = models.IPAddressField(
        _("IP Address of the Article Creator"),
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    last_update = models.DateTimeField(
        auto_now=True,
        auto_now_add=True,
        db_index=True
    )
    removed = models.BooleanField(
        _("Is removed?"),
        default=False,
        db_index=True
    )

    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True, db_index=True)
    group = generic.GenericForeignKey('content_type', 'object_id')

    tags = TagField()

    objects = QuerySetManager()

    non_removed_objects = NonRemovedArticleManager()

    class QuerySet(QuerySet):

        def get_by(self, title, group=None):
            if group is None:
                return self.get(object_id=None, title=title)
            return group.content_objects(self.filter(title=title)).get()

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.group is None:
            return urlresolvers.reverse(
                'wiki_article',
                kwargs={'title': self.title, }
            )
        #return self.group.get_absolute_url() + 'wiki/' + self.title
        return self.group.content_bridge.reverse(
            'wiki_article', self.group,
            kwargs={'title': self.title, }
        )

    def mark_removed(self):
        """ Mark the Article as 'removed'."""
        if not self.removed:
            self.removed = True
            self.save()

    def is_allowed(self, user, perm=None):
        """Checks permissions."""
        if self.group:
            if perm in ('wiki.view_article',
                        'wiki.browse_article', ):
                return user.has_perm('view', self.group)

            if perm in ('wiki.add_article',  # hierarchical?
                        'wiki.change_article',
                        'wiki.browse_revision_article',
                        'wiki.reapply_revision_article', ):
                return self.group.user_is_member(user)

            if perm in ('comments.add_comment', ):
                return self.group.user_is_member(user) or\
                    user.has_perm(perm, self.group) or\
                    user.has_perm('wiki.comment_article', self.group)

            if perm in ('wiki.mark_removed_article',
                        'wiki.delete_article',
                        'comments.change_comment',
                        'comments.delete_comment', ):
                return user.has_perm(perm, self.group)

        else:
            if perm in ('wiki.view_article',
                        'wiki.browse_article', ):
                return True

            if perm in ('wiki.add_article',
                        'wiki.change_article',
                        'wiki.browse_revision_article',
                        'wiki.reapply_revision_article',
                        'comments.add_comment', ):
                return user.is_authenticated()

            if perm in ('wiki.mark_removed_article',
                        'wiki.delete_article',
                        'comments.change_comment',
                        'comments.delete_comment', ):
                return False

        return False

    def latest_changeset(self):
        try:
            return revisions_for_object(self)[0]
        except IndexError:
            return None

if notification is not None:
    signals.post_save.connect(notification.handle_observations, sender=Article)


def wiki_article_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Article):
        article = instance.content_object
        # Article.objects.filter(pk=article.pk).update(last_update=datetime.now())  # Don't send a signal
        if notification and kwargs.get('created'):
            current_site = Site.objects.get_current()
            group = article.group
            notice_uid = 'wiki_article_comment_{0}_{1}'.format(
                current_site.pk,
                instance.pk
            )

            notification.send_observation_notices_for(
                article, 'wiki_article_comment', extra_context={
                    "user": instance.user,
                    "article": article,
                    "comment": instance,
                    "group": group,
                    "context_object": instance,
                    "notice_uid": notice_uid,
                }
            )

            notify_list = [article.creator.pk, ]
            current_site = Site.objects.get_current()
            notify_list += ThreadedComment.objects.for_model(article).filter(
                is_public=True,
                is_removed=False,
                site=current_site,
                object_pk=article.pk
            ).values_list('user', flat=True)
            notify_list = list(set(notify_list))
            if instance.user.pk in notify_list:
                notify_list.remove(instance.user.pk)
            notification.send(notify_list, "wiki_article_comment", {
                "user": instance.user,
                "article": article,
                "comment": instance,
                "group": group,
                "notice_uid": notice_uid,
            })

models.signals.post_save.connect(wiki_article_comment, sender=ThreadedComment)

versioning.register(Article, ['title', 'content', 'summary', 'markup', ])

# Python 2.* compatible
try:
    unicode
except NameError:
    pass
else:
    for cls in (Article, ):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
