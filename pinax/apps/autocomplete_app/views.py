from __future__ import absolute_import, unicode_literals
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import simplejson

# @@@ these can be cleaned up a lot, made more generic and with better queries


def username_autocomplete_all(request):
    """
    Provides username matching based on matches of the beginning of the
    usernames of all users in the system.
    """
    if request.user.is_authenticated():
        from django.contrib.auth.models import User
        from avatar.templatetags.avatar_tags import avatar
        q = request.GET.get("term", "").rstrip(", ")
        q = q.split(',').pop().strip()

        try:
            limit = int(request.GET["limit"])
        except (KeyError, ValueError):
            limit = 10
        if limit > 100:
            limit = 100

        content = []
        if q:
            users = User.objects.filter(is_active=True, username__istartswith=q).order_by("username")[:limit]
            # @@@ temporary hack -- don't try this at home (or on real sites)
            for user in users:
                try:
                    profile = user.get_profile()
                    entry = {
                        'label': user.username,
                        'value': user.username,
                        'avatar': avatar(user, 40),
                        'location': profile.location,
                    }
                    content.append(entry)
                except ObjectDoesNotExist:
                    pass
        response = HttpResponse(simplejson.dumps(list(content)),
                                mimetype='application/json')
    else:
        response = HttpResponseForbidden()
    setattr(response, "djangologging.suppress_output", True)
    return response


def username_autocomplete_friends(request):
    """
    Provides username matching based on matches of the beginning of the
    usernames of friends.
    """
    if request.user.is_authenticated():
        from friends.models import Friendship
        from avatar.templatetags.avatar_tags import avatar
        q = request.GET.get("term", "").rstrip(", ")
        q = q.split(',').pop().strip()

        try:
            limit = int(request.GET["limit"])
        except (KeyError, ValueError):
            limit = 10
        if limit > 100:
            limit = 100

        content = []
        if q:
            friends = Friendship.objects.friends_for_user(request.user)
            for friendship in friends:
                if friendship["friend"].is_active and\
                        friendship["friend"].username.lower().startswith(q.lower()):
                    try:
                        profile = friendship["friend"].get_profile()
                        entry = {
                            'label': friendship["friend"].username,
                            'value': friendship["friend"].username,
                            'avatar': avatar(friendship["friend"], 40),
                            'location': profile.location,
                        }
                        content.append(entry)
                    except ObjectDoesNotExist:
                        pass
        response = HttpResponse(simplejson.dumps(list(content)),
                                mimetype='application/json')
    else:
        response = HttpResponseForbidden()
    setattr(response, "djangologging.suppress_output", True)
    return response
