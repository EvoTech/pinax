# -*- coding: utf-8 -*-

import os
import hashlib
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.core.cache import cache
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import (Http404, HttpResponseRedirect,
                         HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden)
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.syndication.views import FeedDoesNotExist

from pinax.apps.wiki.forms import ArticleForm, SearchForm
from pinax.apps.wiki.models import Article, ChangeSet
from pinax.apps.wiki.feeds import (RssArticleHistoryFeed, AtomArticleHistoryFeed,
                        RssHistoryFeed, AtomHistoryFeed)
from pinax.apps.wiki.utils import get_ct, login_required


# Settings

#  lock duration in minutes
try:
    WIKI_LOCK_DURATION = settings.WIKI_LOCK_DURATION
except AttributeError:
    WIKI_LOCK_DURATION = 15

try:
    from notification import models as notification
except ImportError:
    notification = None

# default querysets
ALL_ARTICLES = Article.non_removed_objects.all()
ALL_CHANGES = ChangeSet.objects.all()


def group_and_bridge(request):
    """
    Given the request we can depend on the GroupMiddleware to provide the
    group and bridge.
    """
    
    # be group aware
    group = getattr(request, "group", None)
    if group:
        bridge = request.bridge
    else:
        bridge = None
    
    return group, bridge


def group_context(group, bridge):
    # @@@ use bridge
    ctx = {
        "group": group,
    }
    if group:
        ctx["group_base"] = bridge.group_base_template()
    return ctx


def get_real_ip(request):
    """ Returns the real user IP, even if behind a proxy.
    Set BEHIND_PROXY to True in your settings if Django is
    running behind a proxy.
    """
    if getattr(settings, 'BEHIND_PROXY', False):
        return request.META['HTTP_X_FORWARDED_FOR']
    return request.META['REMOTE_ADDR']


def get_articles_by_group(article_qs, group=None, bridge=None):
    if group:
        article_qs = group.content_objects(article_qs)
    else:
        article_qs = article_qs.filter(object_id=None)
    return article_qs, group


def get_articles_for_object(object, article_qs=None):
    if article_qs is None:
        article_qs = ALL_ARTICLES
    return article_qs.filter( content_type=get_ct(object),
                                       object_id=object.id)


def get_url(urlname, group=None, args=None, kw=None, bridge=None):
    if group is None:
        # @@@ due to group support passing args isn't really needed
        return reverse(urlname, args=args, kwargs=kw)
    else:
        return bridge.reverse(urlname, group, kwargs=kw)


class ArticleEditLock(object):
    """ A soft lock to edting an article.
    """

    def __init__(self, title, request, message_template=None):
        self.title = title
        self.user_ip = get_real_ip(request)
        self.user = request.user
        self.created_at = datetime.now()

        if message_template is None:
            message_template = _('Possible edit conflict:' +\
            ' another user started editing this article %s min. ago.')

        self.message_template = message_template
        
        cache.set(self.__class__.get_cache_name(title), self,
                  WIKI_LOCK_DURATION * 60)

    @classmethod
    def get(cls, title, request, message_template=None):
        instance = cache.get(cls.get_cache_name(title), None)
        if instance is None:
            instance = cls(title, request, message_template)
        return instance

    @classmethod
    def unlock(cls, title):
        cache.delete(cls.get_cache_name(title))

    @classmethod
    def get_cache_name(cls, name):
        name_hash = hashlib.md5(unicode(name).encode('utf-8')).hexdigest()
        return 'wiki_article_lock_{0}'.format(name_hash)

    def create_message(self, request):
        """ Send a message to the user if there is another user
        editing this article.
        """
        if not self.is_mine(request):
            delt = datetime.now() - self.created_at
            messages.warning(
                request,
                self.message_template % (int(delt.seconds / 60) or 1)
            )

    def is_mine(self, request):
        if self.user.is_authenticated() or request.user.is_authenticated():
            return self.user == request.user
        return self.user_ip == get_real_ip(request)


def has_read_perm(user, group, is_member, is_private):
    """ Return True if the user has permission to *read*
    Articles, False otherwise.
    """
    if group:
        return user.has_perm('view', group)
    return True

def has_write_perm(user, group, is_member):
    """ Return True if the user have permission to edit Articles,
    False otherwise.
    """
    if group:
        if is_member is not None:
            return is_member(user, group)
        else:
            return group.user_is_member(user)
    return user.is_authenticated()


#@login_required
def article_list(request,
                 group_slug=None, bridge=None,
                 article_qs=ALL_ARTICLES,
                 ArticleClass=Article,
                 SearchFormClass=SearchForm,
                 template_name='index.html',
                 template_dir='wiki',
                 extra_context=None,
                 is_member=None,
                 is_private=None,
                 *args, **kw):
    if request.method == 'GET':
        group, bridge = group_and_bridge(request)
        articles, group = get_articles_by_group(article_qs, group, bridge)

        allow_read = has_read_perm(request.user, group, is_member, is_private)
        allow_write = has_write_perm(request.user, group, is_member)

        if not allow_read:
            return HttpResponseForbidden()

        articles = articles.order_by('-created_at')

        search_form = SearchFormClass()

        template_params = {'articles': articles,
                           'search_form': search_form,
                           'allow_write': allow_write,
                           'group': group}

        if group:
            new_article = ArticleClass(title="NewArticle",
                                       content_type=get_ct(group),
                                       object_id=group.id)
        else:
            new_article = ArticleClass(title="NewArticle")
        template_params['new_article'] = new_article
        if extra_context is not None:
            template_params.update(extra_context)

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))
    return HttpResponseNotAllowed(['GET'])

#patched
#@login_required
def view_article(request, title,
                 ArticleClass=Article, # to create an unsaved instance
                 group_slug=None, bridge=None,
                 article_qs=ALL_ARTICLES,
                 template_name='view.html',
                 template_dir='wiki',
                 extra_context=None,
                 is_member=None,
                 is_private=None,
                 *args, **kw):

    if request.method == 'GET':
        group, bridge = group_and_bridge(request)
        allow_read = has_read_perm(request.user, group, is_member, is_private)
        allow_write = has_write_perm(request.user, group, is_member)

        try:
            article = article_qs.get_by(title, group)
            allow_read = request.user.has_perm('wiki.view_article', article)
            allow_write = request.user.has_perm('wiki.change_article', article)
            if notification is not None:
                is_observing = notification.is_observing(article, request.user)
            else:
                is_observing = False
        except ArticleClass.DoesNotExist:
            article = ArticleClass(title=title)
            is_observing = False

        if not allow_read:
            return HttpResponseForbidden()

        template_params = {'article': article,
                           'allow_write': allow_write}

        if notification is not None:
            template_params.update({'is_observing': is_observing,
                                    'can_observe': True})

        template_params['group'] = group
        if extra_context is not None:
            template_params.update(extra_context)

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))
    return HttpResponseNotAllowed(['GET'])


@login_required
def edit_article(request, title,
                 group_slug=None, bridge=None,
                 article_qs=ALL_ARTICLES,
                 ArticleClass=Article, # to get the DoesNotExist exception
                 ArticleFormClass=ArticleForm,
                 template_name='edit.html',
                 template_dir='wiki',
                 extra_context=None,
                 check_membership=False,
                 is_member=None,
                 is_private=None,
                 *args, **kw):
    group, bridge = group_and_bridge(request)
    allow_read = has_read_perm(request.user, group, is_member, is_private)
    allow_write = has_write_perm(request.user, group, is_member)

    try:
        article = article_qs.get_by(title, group)
        allow_read = request.user.has_perm('wiki.view_article', article)
        allow_write = request.user.has_perm('wiki.change_article', article)
    except ArticleClass.DoesNotExist:
        article = None

    if not allow_write:
        return HttpResponseForbidden()

    if request.method == 'POST':

        form = ArticleFormClass(request.POST, instance=article)

        if form.is_valid():

            if request.user.is_authenticated():
                form.editor = request.user
                if article is None:
                    user_message = u"Your article was created successfully."
                else:
                    user_message = u"Your article was edited successfully."
                request.user.message_set.create(message=user_message)

            if ((article is None) and group):
                form.group = group

            new_article, changeset = form.save()
            ArticleEditLock.unlock(title)

            url = get_url('wiki_article', group, kw={
                'title': new_article.title,
            }, bridge=bridge)

            return HttpResponseRedirect(url)

    elif request.method == 'GET':
        user_ip = get_real_ip(request)

        lock = ArticleEditLock.get(title, request)
        lock.create_message(request)

        initial = {'user_ip': user_ip}
        if group:
            # @@@ wikiapp currently handles the group filtering, but we will
            # eventually want to handle that via the bridge.
            initial.update({'content_type': get_ct(group).id,
                            'object_id': group.id})

        if article is None:
            initial.update({'title': title,
                            'action': 'create'})
            form = ArticleFormClass(initial=initial)
        else:
            initial['action'] = 'edit'
            form = ArticleFormClass(instance=article,
                                    initial=initial)

    template_params = {'form': form}

    template_params['group'] = group
    if extra_context is not None:
        template_params.update(extra_context)

    return render_to_response(os.path.join(template_dir, template_name),
                              template_params,
                              context_instance=RequestContext(request))


@login_required
def remove_article(request, title,
                   group_slug=None, bridge=None,
                   article_qs=ALL_ARTICLES,
                   template_name='confirm_remove.html',
                   template_dir='wiki',
                   extra_context=None,
                   is_member=None,
                   is_private=None,
                   *args, **kw):
    """ Show a confirmation page on GET, delete the article on POST.
    """
    group, bridge = group_and_bridge(request)

    if request.method == 'GET':

        article = article_qs.get_by(title, group)
        if not request.user.has_perm('wiki.delete_article', article):
            raise PermissionDenied()

        request.session['article_to_remove'] = article

        template_params = {'article': article}
        template_params['group'] = group
        if extra_context:
            template_params.update(extra_context)

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))

    elif request.method == 'POST':

        article = request.session['article_to_remove']
        if not request.user.has_perm('wiki.mark_removed_article', article):
            raise PermissionDenied()
        article.mark_removed()

        return HttpResponseRedirect(get_url('wiki_index', group, bridge=bridge))

    return HttpResponseNotAllowed(['GET', 'POST'])


@login_required
def view_changeset(request, title, revision,
                   group_slug=None, bridge=None,
                   article_qs=ALL_ARTICLES,
                   changes_qs=ALL_CHANGES,
                   template_name='changeset.html',
                   template_dir='wiki',
                   extra_context=None,
                   is_member=None,
                   is_private=None,
                   *args, **kw):

    if request.method == "GET":
        article_args = {'article__title': title}
        group, bridge = group_and_bridge(request)

        if group:
            # @@@ hmm, need to look into this for the bridge i think
            article_args.update({'article__content_type': get_ct(group),
                                 'article__object_id': group.id})
        else:
            article_args.update({'article__object_id': None})

        changeset = get_object_or_404(
            changes_qs.select_related(),
            revision=int(revision),
            **article_args)

        article = changeset.article
        allow_read = request.user.has_perm('wiki.view_article', article)
        allow_write = request.user.has_perm('wiki.change_article', article)

        if not allow_read:
            return HttpResponseForbidden()

        template_params = {'article': article,
                           'article_title': article.title,
                           'changeset': changeset,
                           'allow_write': allow_write}

        template_params['group'] = group
        if extra_context is not None:
            template_params.update(extra_context)

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))
    return HttpResponseNotAllowed(['GET'])


@login_required
def article_history(request, title,
                    group_slug=None, bridge=None,
                    article_qs=ALL_ARTICLES,
                    template_name='history.html',
                    template_dir='wiki',
                    extra_context=None,
                    is_member=None,
                    is_private=None,
                    *args, **kw):

    if request.method == 'GET':

        article_args = {'title': title}
        group, bridge = group_and_bridge(request)

        if group:
            # @@@ use bridge instead
            article_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
        else:
            article_args.update({'object_id': None})

        article = get_object_or_404(article_qs, **article_args)
        allow_read = request.user.has_perm('wiki.view_article', article)
        allow_write = request.user.has_perm('wiki.change_article', article)

        if not allow_read:
            return HttpResponseForbidden()

        changes = article.changeset_set.all().order_by('-revision')

        template_params = {'article': article,
                           'changes': changes,
                           'allow_write': allow_write}
        template_params['group'] = group
        if extra_context is not None:
            template_params.update(extra_context)

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))

    return HttpResponseNotAllowed(['GET'])


@login_required
def revert_to_revision(request, title,
                       group_slug=None, bridge=None,
                       article_qs=ALL_ARTICLES,
                       extra_context=None,
                       is_member=None,
                       is_private=None,
                       *args, **kw):

    if request.method == 'POST':

        revision = int(request.POST['revision'])

        article_args = {'title': title}

        group, bridge = group_and_bridge(request)

        if group:
            # @@@ use bridge instead
            article_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
        else:
            article_args.update({'object_id': None})

        article = get_object_or_404(article_qs, **article_args)
        allow_read = request.user.has_perm('wiki.view_article', article)
        allow_write = request.user.has_perm('wiki.change_article', article)

        if not allow_write:
            return HttpResponseForbidden()

        if request.user.is_authenticated():
            article.revert_to(revision, get_real_ip(request), request.user)
        else:
            article.revert_to(revision, get_real_ip(request))


        if request.user.is_authenticated():
            request.user.message_set.create(
                message=u"The article was reverted successfully.")

        url = get_url('wiki_article_history', group, kw={
            'title': title,
        }, bridge=bridge)

        return HttpResponseRedirect(url)

    return HttpResponseNotAllowed(['POST'])


@login_required
def search_article(request,
                   group_slug=None, bridge=None,
                   article_qs=ALL_ARTICLES,
                   SearchFormClass=SearchForm,
                   template_name='search_results.html',
                   template_dir='wiki',
                   extra_context=None,
                   is_member=None,
                   is_private=None,
                   *args, **kw):
    if request.method == 'GET':
        articles_by_content = None
        article_by_title = None

        search_term = ''
        if not request.GET:
            search_form = SearchFormClass()
        else:
            search_form = SearchFormClass(request.GET)
            if search_form.is_valid():
                search_term = search_form.cleaned_data.get('q')
                title_only = search_form.cleaned_data.get('title_only')

                group, bridge = group_and_bridge(request)
                allow_read = has_read_perm(request.user, group, is_member,
                                           is_private)
                allow_write = has_write_perm(request.user, group, is_member)

                if not allow_read:
                    return HttpResponseForbidden()

                articles, group = get_articles_by_group(article_qs, group,
                                                        bridge)
                articles = articles.order_by('-created_at')

                url = None
                if title_only:
                    # go to article by title
                    url = get_url('wiki_article', group, kw={
                        'title': search_term,
                    }, bridge=bridge)
                else:
                    articles_by_content = articles.filter(
                        Q(content__icontains=search_term)
                        | Q(summary__icontains=search_term))

                    try:
                        article_by_title = articles.get_by(search_term, group)
                    except ObjectDoesNotExist:
                        pass

                    if article_by_title is not None:
                        if not articles_by_content.count():
                            url = article_by_title.get_absolute_url()
                    elif articles_by_content.count() == 1:
                        url = articles_by_content.get().get_absolute_url()

                if url is not None:
                    return HttpResponseRedirect(url)

        template_params = {
            'search_form': search_form,
            'search_term': search_term,
            'articles_by_content': articles_by_content,
            'article_by_title': article_by_title,
            'group': group,
        }

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))

    return HttpResponseNotAllowed(['GET'])


@login_required
def history(request,
            group_slug=None, bridge=None,
            article_qs=ALL_ARTICLES, changes_qs=ALL_CHANGES,
            template_name='recentchanges.html',
            template_dir='wiki',
            extra_context=None,
            is_member=None,
            is_private=None,
            *args, **kw):

    if request.method == 'GET':
        group, bridge = group_and_bridge(request)
        allow_read = has_read_perm(request.user, group, is_member, is_private)
        allow_write = has_write_perm(request.user, group, is_member)

        if not allow_read:
            return HttpResponseForbidden()

        if group:
            changes_qs = changes_qs.filter(article__content_type=get_ct(group),
                                           article__object_id=group.id)
        else:
            changes_qs = changes_qs.filter(article__object_id=None)

        template_params = {'changes': changes_qs.order_by('-modified'),
                           'allow_write': allow_write}
        template_params['group'] = group

        if extra_context is not None:
            template_params.update(extra_context)

        return render_to_response(os.path.join(template_dir, template_name),
                                  template_params,
                                  context_instance=RequestContext(request))
    return HttpResponseNotAllowed(['GET'])


@login_required
def observe_article(request, title,
                    group_slug=None, bridge=None,
                    article_qs=ALL_ARTICLES,
                    template_name='recentchanges.html',
                    template_dir='wiki',
                    extra_context=None,
                    is_member=None,
                    is_private=None,
                    *args, **kw):
    if request.method == 'POST':

        article_args = {'title': title}
        group, bridge = group_and_bridge(request)

        if group:
            article_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})

        article = get_object_or_404(article_qs, **article_args)
        allow_read = request.user.has_perm('wiki.view_article', article)
        allow_write = request.user.has_perm('wiki.change_article', article)

        if not allow_read:
            return HttpResponseForbidden()

        notification.observe(article, request.user,
                             'wiki_observed_article_changed')

        url = get_url('wiki_article', group, kw={
            'title': article.title,
        }, bridge=bridge)

        return HttpResponseRedirect(url)

    return HttpResponseNotAllowed(['POST'])


@login_required
def stop_observing_article(request, title,
                           group_slug=None, bridge=None,
                           article_qs=ALL_ARTICLES,
                           template_name='recentchanges.html',
                           template_dir='wiki',
                           extra_context=None,
                           is_member=None,
                           is_private=None,
                           *args, **kw):
    if request.method == 'POST':

        article_args = {'title': title}
        group, bridge = group_and_bridge(request)

        if group:
            article_args.update({'content_type': get_ct(group),
                                 'object_id': group.id})
        else:
            article_args.update({'object_id': None})

        article = get_object_or_404(article_qs, **article_args)
        allow_read = request.user.has_perm('wiki.view_article', article)
        allow_write = request.user.has_perm('wiki.change_article', article)

        if not allow_read:
            return HttpResponseForbidden()

        notification.stop_observing(article, request.user)

        url = get_url('wiki_article', group, kw={
            'title': article.title,
        }, bridge=bridge)

        return HttpResponseRedirect(url)
    return HttpResponseNotAllowed(['POST'])


def article_history_feed(request, feedtype, title,
                         group_slug=None, bridge=None,
                         article_qs=ALL_ARTICLES, changes_qs=ALL_CHANGES,
                         extra_context=None,
                         is_member=None,
                         is_private=None,
                         *args, **kw):
    group, bridge = group_and_bridge(request)
    feeds = {'rss' : RssArticleHistoryFeed,
             'atom' : AtomArticleHistoryFeed}
    ArticleHistoryFeed = feeds.get(feedtype, RssArticleHistoryFeed)

    try:
        feedgen = ArticleHistoryFeed(title, request,
                                     group.slug, bridge,
                                     article_qs, changes_qs,
                                     extra_context,
                                     *args, **kw).get_feed(title)
    except FeedDoesNotExist:
        raise Http404

    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response


def history_feed(request, feedtype,
                 group_slug=None, bridge=None,
                 article_qs=ALL_ARTICLES, changes_qs=ALL_CHANGES,
                 extra_context=None,
                 is_member=None,
                 is_private=None,
                 *args, **kw):
    group, bridge = group_and_bridge(request)
    feeds = {'rss' : RssHistoryFeed,
             'atom' : AtomHistoryFeed}
    HistoryFeed = feeds.get(feedtype, RssHistoryFeed)

    try:
        feedgen = HistoryFeed(request,
                              group.slug, bridge,
                              article_qs, changes_qs,
                              extra_context,
                              *args, **kw).get_feed()
    except FeedDoesNotExist:
        raise Http404

    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response
