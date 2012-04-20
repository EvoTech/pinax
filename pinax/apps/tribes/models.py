from django.contrib.auth.models import  User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from groups.base import Group

MEMBER_STATUSES = [
    ('inactive', _(u"inactive")),
    ('requested', _(u"requested")),
    ('invited', _(u"invited")),
    ('active', _(u"active")),
    ('blocked', _(u"blocked")),
]


class Tribe(Group):
    
    member_users = models.ManyToManyField(
        User,
        through = "TribeMember",
        verbose_name = _("members")
    )
    # private means only members can see the tribe
    private = models.BooleanField(_("private"), default=False)
    
    def get_absolute_url(self):
        return reverse("tribe_detail", kwargs={"group_slug": self.slug})

    def member_queryset(self):
        return User.objects.filter(
            tribes__status='active',
            tribes__tribe=self,
        )

    def user_is_member(self, user):
        if not user.is_authenticated():
            return False
        return TribeMember.objects.filter(
            status='active',
            tribe=self,
            user=user
        ).exists()


class TribeMember(models.Model):
    """Tribe member"""

    status = models.CharField(
        verbose_name=_("Status"),
        max_length=10,
        choices=MEMBER_STATUSES,
        default='inactive',
        db_index=True
    )
    tribe = models.ForeignKey(
        Tribe,
        related_name = "members",
        verbose_name = _("tribe")
    )
    user = models.ForeignKey(
        User,
        related_name = "tribes",
        verbose_name = _("user")
    )

    class Meta:
        unique_together = [("user", "tribe")]
