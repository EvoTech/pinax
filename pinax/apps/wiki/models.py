from datetime import datetime
from django.core import urlresolvers

# Google Diff Match Patch library
# http://code.google.com/p/google-diff-match-patch
from diff_match_patch import diff_match_patch

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.query import QuerySet

from tagging.fields import TagField
from tagging.models import Tag
from threadedcomments.models import ThreadedComment

from pinax.apps.wiki.utils import get_ct

try:
    from notification import models as notification
    from django.db.models import signals
except ImportError:
    notification = None

# We dont need to create a new one everytime
dmp = diff_match_patch()

def diff(txt1, txt2):
    """Create a 'diff' from txt1 to txt2."""
    patch = dmp.patch_make(txt1, txt2)
    return dmp.patch_toText(patch)

try:
    markup_choices = settings.WIKI_MARKUP_CHOICES
except AttributeError:
    markup_choices = (
        ('creole', _(u'Creole')),
        ('restructuredtext', _(u'reStructuredText')),
        ('textile', _(u'Textile')),
        ('markdown', _(u'Markdown')),
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
    title = models.CharField(_(u"Title"), max_length=255, db_index=True)
    content = models.TextField(_(u"Content"))
    summary = models.CharField(_(u"Summary"), max_length=255,
                               null=True, blank=True, db_index=True)
    markup = models.CharField(_(u"Content Markup"), max_length=100,
                              choices=markup_choices,
                              null=True, blank=True)
    creator = models.ForeignKey(User, verbose_name=_('Article Creator'),
                                null=True)
    creator_ip = models.IPAddressField(_("IP Address of the Article Creator"),
                                       blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_update = models.DateTimeField(auto_now=True, auto_now_add=True, db_index=True)
    removed = models.BooleanField(_("Is removed?"), default=False, db_index=True)

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
        verbose_name = _(u'Article')
        verbose_name_plural = _(u'Articles')

    def get_absolute_url(self):
        if self.group is None:
            return urlresolvers.reverse('wiki_article', kwargs={'title': self.title, })
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

    def latest_changeset(self):
        try:
            return self.changeset_set.filter(
                reverted=False).order_by('-revision')[0]
        except IndexError:
            return ChangeSet.objects.none()

    def new_revision(self, old_content, old_title, old_markup,
                     comment, editor_ip, editor):
        '''Create a new ChangeSet with the old content.'''

        content_diff = diff(self.content, old_content)

        cs = ChangeSet.objects.create(
            article=self,
            comment=comment,
            editor_ip=editor_ip,
            editor=editor,
            old_title=old_title,
            old_markup=old_markup,
            content_diff=content_diff)

        if None not in (notification, self.creator):
            if self.group:
                notify_list = self.group.member_queryset()
                if editor:
                    notify_list = notify_list.exclude(id__exact=editor.id)
            else:
                notify_list = [self.creator]

            # Fix pickle problem
            article = self.__class__.objects.get(pk=self.pk)

            notification.send(notify_list, "wiki_article_edited",
                              {'article': article, 'user': (editor or editor_ip),
                               'context_object': article, })

        return cs

    def revert_to(self, revision, editor_ip, editor=None):
        """ Revert the article to a previuos state, by revision number.
        """
        changeset = self.changeset_set.get(revision=revision)
        changeset.reapply(editor_ip, editor)


    def __unicode__(self):
        return self.title

    def is_allowed(self, user, perm=None):
        """Checks permissions."""
        if self.group:
            if perm in ('wiki.view_article',
                        'wiki.browse_article', ):
                return user.has_perm('view', self.group)

            if perm in ('wiki.add_article',  # hierarchical?
                        'wiki.change_article', ):
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

            if perm in ('wiki.observe_wiki_observed_article_changed_article',
                        'wiki.observe_wiki_article_edited_article',
                        'wiki.observe_wiki_revision_reverted_article',
                        'wiki.observe_wiki_article_comment_article', ):
                return self.group.user_is_member(user)

        else:
            if perm in ('wiki.view_article',
                        'wiki.browse_article', ):
                return True

            if perm in ('wiki.add_article',
                        'wiki.change_article',
                        'comments.add_comment', ):
                return user.is_authenticated()

            if perm in ('wiki.mark_removed_article',
                        'wiki.delete_article',
                        'comments.change_comment', 
                        'comments.delete_comment', ):
                return False

            if perm in ('wiki.observe_wiki_observed_article_changed_article',
                        'wiki.observe_wiki_article_edited_article',
                        'wiki.observe_wiki_revision_reverted_article',
                        'wiki.observe_wiki_article_comment_article', ):
                return user.is_authenticated()

        return False


class NonRevertedChangeSetManager(QuerySetManager):

    def get_default_queryset(self):
        super(NonRevertedChangeSetManager, self).get_query_set().filter(
              reverted=False)


class ChangeSet(models.Model):
    """A report of an older version of some Article."""

    article = models.ForeignKey(Article, verbose_name=_(u"Article"))

    # Editor identification -- logged or anonymous
    editor = models.ForeignKey(User, verbose_name=_(u'Editor'),
                               null=True)
    editor_ip = models.IPAddressField(_(u"IP Address of the Editor"))

    # Revision number, starting from 1
    revision = models.IntegerField(_(u"Revision Number"))

    # How to recreate this version
    old_title = models.CharField(_(u"Old Title"), max_length=50, blank=True)
    old_markup = models.CharField(_(u"Article Content Markup"), max_length=100,
                                  choices=markup_choices,
                                  null=True, blank=True)
    content_diff = models.TextField(_(u"Content Patch"), blank=True)

    comment = models.CharField(_(u"Editor comment"), max_length=50, blank=True)
    modified = models.DateTimeField(_(u"Modified at"), default=datetime.now)
    reverted = models.BooleanField(_(u"Reverted Revision"), default=False)

    objects = QuerySetManager()
    non_reverted_objects = NonRevertedChangeSetManager()

    class QuerySet(QuerySet):
        def all_later(self, revision):
            """ Return all changes later to the given revision.
            Util when we want to revert to the given revision.
            """
            return self.filter(revision__gt=int(revision))


    class Meta:
        verbose_name = _(u'Change set')
        verbose_name_plural = _(u'Change sets')
        get_latest_by  = 'modified'
        ordering = ('-revision',)

    def __unicode__(self):
        return u'#%s' % self.revision

    @models.permalink
    def get_absolute_url(self):
        if self.article.group is None:
            return ('wiki_changeset', (),
                    {'title': self.article.title,
                     'revision': self.revision})
        return ('wiki_changeset', (),
                {'group_slug': self.article.group.slug,
                 'title': self.article.title,
                 'revision': self.revision})


    def is_anonymous_change(self):
        return self.editor is None

    def reapply(self, editor_ip, editor):
        """ Return the Article to this revision.
        """

        # XXX Would be better to exclude reverted revisions
        #     and revisions previous/next to reverted ones
        next_changes = self.article.changeset_set.filter(
            revision__gt=self.revision).order_by('-revision')

        article = self.article

        content = None
        for changeset in next_changes:
            if content is None:
                content = article.content
            patch = dmp.patch_fromText(changeset.content_diff)
            content = dmp.patch_apply(patch, content)[0]

            changeset.reverted = True
            changeset.save()

        old_content = article.content
        old_title = article.title
        old_markup = article.markup

        article.content = content
        article.title = changeset.old_title
        article.markup = changeset.old_markup
        article.save()

        article.new_revision(
            old_content=old_content, old_title=old_title,
            old_markup=old_markup,
            comment="Reverted to revision #%s" % self.revision,
            editor_ip=editor_ip, editor=editor)

        self.save()

        if None not in (notification, self.editor):
            notification.send([self.editor], "wiki_revision_reverted",
                              {'revision': self, 'article': self.article,
                               'context_object': article, })

    def save(self, *args, **kwargs):
        """ Saves the article with a new revision.
        """
        if self.id is None:
            try:
                self.revision = ChangeSet.objects.filter(
                    article=self.article).latest().revision + 1
            except self.DoesNotExist:
                self.revision = 1
        super(ChangeSet, self).save(*args, **kwargs)

    def display_diff(self):
        ''' Returns a HTML representation of the diff.
        '''

        # well, it *will* be the old content
        old_content = self.article.content

        # newer non-reverted revisions of this article, starting from this
        newer_changesets = ChangeSet.non_reverted_objects.filter(
            article=self.article,
            revision__gte=self.revision)

        # apply all patches to get the content of this revision
        for i, changeset in enumerate(newer_changesets):
            patches = dmp.patch_fromText(changeset.content_diff)
            if len(newer_changesets) == i+1:
                # we need to compare with the next revision after the change
                next_rev_content = old_content
            old_content = dmp.patch_apply(patches, old_content)[0]

        diffs = dmp.diff_main(old_content, next_rev_content)
        return dmp.diff_prettyHtml(diffs)

if notification is not None:
    signals.post_save.connect(notification.handle_observations, sender=Article)


def wiki_article_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Article):
        article = instance.content_object
        # Article.objects.filter(pk=article.pk).update(last_update=datetime.now())  # Don't send a signal
        if notification:
            group = article.group
            notify_list = [article.creator.pk, ]
            from django.contrib.sites.models import Site
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
            })

models.signals.post_save.connect(wiki_article_comment, sender=ThreadedComment)
