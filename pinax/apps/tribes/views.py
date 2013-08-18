from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from pinax.apps.tribes.models import Tribe, TribeMember, TribeMemberHistory
from pinax.apps.tribes.forms import TribeForm, TribeUpdateForm

TOPIC_COUNT_SQL = """
SELECT COUNT(*)
FROM topics_topic
WHERE
    topics_topic.object_id = tribes_tribe.id AND
    topics_topic.content_type_id = %s
"""
MEMBER_COUNT_SQL = """
SELECT COUNT(*)
FROM tribes_tribemember
WHERE tribes_tribemember.tribe_id = tribes_tribe.id
AND tribes_tribemember.status='active'
"""


@login_required
def create(request, form_class=TribeForm, template_name="tribes/create.html"):
    tribe_form = form_class(request.POST or None)
    
    if tribe_form.is_valid():
        tribe = tribe_form.save(commit=False)
        tribe.creator = request.user
        tribe.save()
        member = TribeMember(
            status='active',
            tribe=tribe,
            user=request.user
        )
        tribe.members.add(member)
        if notification:
            # @@@ might be worth having a shortcut for sending to all users
            notification.send(User.objects.all(), "tribes_new_tribe", {
                "tribe": tribe
            }, queue=True)
        return HttpResponseRedirect(tribe.get_absolute_url())
    
    return render_to_response(template_name, {
        "tribe_form": tribe_form,
    }, context_instance=RequestContext(request))


def tribes(request, template_name="tribes/tribes.html"):
    
    tribes = Tribe.objects.all()
    
    search_terms = request.GET.get("search", "")
    if search_terms:
        tribes = (tribes.filter(name__icontains=search_terms) |
            tribes.filter(description__icontains=search_terms))
    
    content_type = ContentType.objects.get_for_model(Tribe)
    
    tribes = tribes.extra(
        select=SortedDict([
            ("member_count", MEMBER_COUNT_SQL),
            ("topic_count", TOPIC_COUNT_SQL),
        ]),
        select_params=(content_type.id,)
    ).order_by("-topic_count", "-member_count", "name")
    
    return render_to_response(template_name, {
        "tribes": tribes,
        "search_terms": search_terms,
    }, context_instance=RequestContext(request))


def delete(request, group_slug=None, redirect_url=None):
    tribe = get_object_or_404(Tribe, slug=group_slug)
    if not redirect_url:
        redirect_url = reverse("tribe_list")
    
    # @@@ eventually, we'll remove restriction that tribe.creator can't leave
    # tribe but we'll still require tribe.member_queryset().all().count() == 1
    if (request.user.is_authenticated() and request.method == "POST" and
            request.user.has_perm('tribes.delete_tribe', tribe) and
            tribe.member_queryset().all().count() == 1):
        tribe.delete()
        messages.add_message(request, messages.SUCCESS,
            ugettext("Tribe %(tribe_name)s deleted.") % {
                "tribe_name": tribe.name
            }
        )
        # no notification required as the deleter must be the only member
    
    return HttpResponseRedirect(redirect_url)


@login_required
def your_tribes(request, template_name="tribes/your_tribes.html"):

    content_type = ContentType.objects.get_for_model(Tribe)
    tribes = Tribe.objects.extra(
        select=SortedDict([
            ("member_count", MEMBER_COUNT_SQL),
            ("topic_count", TOPIC_COUNT_SQL),
        ]),
        select_params=(content_type.id,)
    ).filter(
        members__user=request.user,
        members__status='active'
    ).order_by("-topic_count", "-member_count", "name")

    return render_to_response(template_name, {
        "tribes": tribes
    }, context_instance=RequestContext(request))


def tribe(request, group_slug=None, form_class=TribeUpdateForm,
          template_name="tribes/tribe.html"):
    tribe = get_object_or_404(Tribe, slug=group_slug)
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        is_member = tribe.user_is_member(request.user)

    action = request.POST.get("action")
    tribe_form = form_class(action == "update" and request.POST or None,
                            instance=tribe)
    if action == "update" and\
            request.user.has_perm('tribes.change_tribe', tribe) and\
            tribe_form.is_valid():
        tribe = tribe_form.save()
    elif action == "join":
        try:
            member = tribe.members.get(user=request.user)
        except:
            member = None
        if is_member:
            messages.add_message(request, messages.WARNING,
                ugettext("You have already joined tribe %(tribe_name)s") % {
                    "tribe_name": tribe.name
                }
            )
        elif member is not None:
            if member.status in ('inactive', 'requested', 'invited', ):
                messages.add_message(request, messages.WARNING,
                    ugettext("You have already joined tribe %(tribe_name)s, but your status is awaiting approval") % {
                        "tribe_name": tribe.name
                    }
                )
            elif member.status == 'blocked':
                messages.add_message(request, messages.WARNING,
                    ugettext("You are blocked for tribe %(tribe_name)s") % {
                        "tribe_name": tribe.name
                    }
                )
        else:
            status = 'inactive' if tribe.private else 'active'
            member = TribeMember.objects.create(
                status=status,
                tribe=tribe,
                user=request.user
            )
            tribe.members.add(member)
            TribeMemberHistory.objects.create(
                member=member,
                status=status,
                message="",
                actor=request.user
            )

            messages.add_message(request, messages.SUCCESS,
                ugettext("You have joined the tribe %(tribe_name)s") % {
                    "tribe_name": tribe.name
                }
            )
            is_member = True
            if notification:
                # Fix pickle problem
                tribe = tribe.__class__.objects.get(pk=tribe.pk)
                notification.send([tribe.creator], "tribes_created_new_member", {
                    "user": request.user,
                    "tribe": tribe
                })
                notification.send(tribe.member_queryset().all(), "tribes_new_member", {
                    "user": request.user,
                    "tribe": tribe
                })
    elif action == "leave":
        member = tribe.members.get(user=request.user)
        if member.status in ('inactive', 'requested', 'invited', 'active', ):
            member.delete()
            messages.add_message(
                request, messages.SUCCESS,
                ugettext("You have left the tribe %(tribe_name)s") % {
                    "tribe_name": tribe.name
                }
            )
            is_member = False
            if notification:
                pass  # @@@ no notification on departure yet
        elif member.status == 'blocked':
            messages.add_message(
                request, messages.SUCCESS,
                ugettext("You are blocked for tribee %(tribe_name)s") % {
                    "tribe_name": tribe.name
                }
            )
            is_member = False
    
    return render_to_response(template_name, {
        "tribe_form": tribe_form,
        "tribe": tribe,
        "group": tribe,  # @@@ this should be the only context var for the tribe
        "is_member": is_member,
    }, context_instance=RequestContext(request))


@login_required
def members(request, group_slug=None, template_name="tribes/members.html", extra_context=None):
    """Members of tribe"""
    tribe = get_object_or_404(Tribe, slug=group_slug)
    if not request.user.has_perm('tribes.view_tribe', tribe):
        raise PermissionDenied
    if extra_context is None:
        extra_context = {}
    users = tribe.member_queryset()
    search_terms = request.GET.get("search", "")
    if search_terms:
        users = users.filter(username__icontains=search_terms)
    return render_to_response(template_name, dict({
        "group": tribe,
        "tribe": tribe,
        "users": users,
        "search_terms": search_terms,
    }, **extra_context), context_instance=RequestContext(request))
