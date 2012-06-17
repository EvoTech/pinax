from __future__ import absolute_import, unicode_literals
from django.contrib.auth.models import  User
from django.core import urlresolvers
from django.db import models
from django.utils.translation import ugettext_lazy as _

from groups.base import Group

MEMBER_STATUSES = [
    ('inactive', _("inactive")),
    ('requested', _("requested")),
    ('invited', _("invited")),
    ('active', _("active")),
    ('blocked', _("blocked")),
]


class Tribe(Group):

    member_users = models.ManyToManyField(
        User,
        through="TribeMember",
        verbose_name=_("members")
    )
    # private means only members can see the tribe
    private = models.BooleanField(_("private"), default=False)

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.slug)

    def get_absolute_url(self):
        return urlresolvers.reverse("tribe_detail", kwargs={"group_slug": self.slug})

    def member_queryset(self):
        return User.objects.filter(
            tribes__status='active',
            tribes__tribe=self,
            is_active=True
        ).order_by("-date_joined")

    def user_is_member(self, user):
        if not user.is_authenticated():
            return False
        return TribeMember.objects.filter(
            status='active',
            tribe=self,
            user=user
        ).exists()

    def is_allowed(self, user, perm=None):
        """Checks permissions."""
        if perm in ('tribes.view_tribe', ):
            return not self.private or self.user_is_member(user)

        if perm  in ('tribes.browse_tribe', ):
            return True

        if perm in ('tribes.add_tribe', ):
            return user.is_authenticated()

        if perm in ('tribes.change_tribe', ):
            return self.creator == user

        if perm in ('tribes.delete_tribe', ):
            return False

        if perm in ('comments.add_comment', ):
            return self.user_is_member(user)

        return False


class TribeMember(models.Model):
    """Tribe member"""

    status = models.CharField(
        verbose_name=_("status"),
        max_length=10,
        choices=MEMBER_STATUSES,
        default='inactive',
        db_index=True
    )
    tribe = models.ForeignKey(
        Tribe,
        related_name="members",
        verbose_name=_("tribe")
    )
    user = models.ForeignKey(
        User,
        related_name="tribes",
        verbose_name=_("user")
    )

    class Meta:
        unique_together = [("user", "tribe")]

    def __unicode__(self):
        return "{0} - {1}".format(self.tribe, self.user)


class TribeRole(models.Model):
    """Tribe's role'"""
    name = models.CharField(_("name"), max_length=50, unique=True)
    title = models.CharField(_("title"), max_length=150, default="")
    description = models.TextField(_("description"), default="")

    def __unicode__(self):
        return self.name


class TribeMemberRole(models.Model):
    """Member roles"""
    member = models.ForeignKey(
        TribeMember,
        verbose_name=_("member"),
        related_name="roles"
    )
    role = models.ForeignKey(
        TribeRole,
        verbose_name=_("role"),
        related_name="members"
    )
    actor = models.ForeignKey(User)
    date = models.DateTimeField(_("date"), auto_now_add=True)

    def __unicode__(self):
        return "{0} - {1}".format(self.member, self.role)


class TribeMemberHistory(models.Model):
    """History of members relations"""
    member = models.ForeignKey(
        TribeMember,
        verbose_name=_("member"),
        related_name="history"
    )
    status = models.CharField(
        verbose_name=_("status"),
        max_length=10,
        choices=MEMBER_STATUSES,
        default='inactive',
        db_index=True
    )
    message = models.TextField(_("message"), default="")
    date = models.DateTimeField(_("date"), auto_now_add=True)
    actor = models.ForeignKey(User)

    def __unicode__(self):
        return "{0} - {1}".format(self.member, self.status)
