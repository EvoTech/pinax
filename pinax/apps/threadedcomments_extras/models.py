from __future__ import absolute_import, unicode_literals
import re
from threadedcomments.models import ThreadedComment

TRANS_RE = re.compile('^threadedcomments\.(.+)_threadedcomment$')

def is_allowed(self, user, perm=None):
    """Checks permissions."""
    perm = TRANS_RE.sub('comments.\\1_comment', perm)
    base_perm = perm.split('.', 1)[1].rsplit('_', 1)[0]

    if perm in ('comments.view_comment',
                'comments.browse_comment', ):
        return user.has_perm(base_perm, self.content_object)

    if perm in ('comments.add_comment', ):
        return user.has_perm(perm, self.content_object) or\
            user.has_perm('comment', self.content_object)

    if perm in ('comments.change_comment', ):
        return False

    if perm in ('comments.delete_comment', ):
        return user.has_perm(perm, self.content_object)

    return False

ThreadedComment.is_allowed = is_allowed
