from django import template
from django.conf import settings
from django.contrib import comments
from django.contrib.auth.decorators import login_required

from django.contrib.comments import signals
from django.contrib.comments.views.utils import next_redirect, confirmation_view
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.csrf import csrf_protect


@csrf_protect
@login_required
def delete(request, comment_id, next=None):
    """
    Deletes a comment. Confirmation on GET, action on POST. Requires the "can
    moderate comments" permission.

    Templates: :template:`comments/delete.html`,
    Context:
        comment
            the flagged `comments.comment` object
    """
    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)

    if not request.user.has_perm('comments.delete_comment', comment):
        raise PermissionDenied

    # Delete on POST
    if request.method == 'POST':
        # Flag the comment as deleted instead of actually deleting it.
        perform_delete(request, comment)
        return next_redirect(request, fallback=next or 'comments-delete-done',
            c=comment.pk)

    # Render a form on GET
    else:
        return render_to_response('comments/delete.html',
            {'comment': comment, "next": next},
            template.RequestContext(request)
        )


def perform_delete(request, comment):
    flag, created = comments.models.CommentFlag.objects.get_or_create(
        comment = comment,
        user    = request.user,
        flag    = comments.models.CommentFlag.MODERATOR_DELETION
    )
    comment.is_removed = True
    comment.save()
    signals.comment_was_flagged.send(
        sender  = comment.__class__,
        comment = comment,
        flag    = flag,
        created = created,
        request = request,
    )


delete_done = confirmation_view(
    template = "comments/deleted.html",
    doc = 'Displays a "comment was deleted" success page.'
)
