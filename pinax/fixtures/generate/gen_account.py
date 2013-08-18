import random

from django.contrib.auth.models import User
from django.template.defaultfilters import capfirst
from django.conf import settings

from pinax.apps.account.models import Account
from timezones.forms import COMMON_TIMEZONE_CHOICES

RSS_FEEDS = (
    'http://www.scripting.com/rss.xml',
    'http://feedproxy.google.com/TechCrunch',
    'http://feeds.feedburner.com/ommalik',
    'http://feedproxy.google.com/fastcompany/scobleizer?format=xml',
    'http://www.djangoproject.com/rss/community/',
)

# TODO: Decide if there's a way we can test twitter and pownce services.

def generate():
    for user in User.objects.all():
        account, created = Account.objects.get_or_create(user = user,
            defaults=dict(
                timezone = random.choice(COMMON_TIMEZONE_CHOICES)[0],
                language = random.choice(settings.LANGUAGES)[0],
            ),
        )
        print "Created User Account: %s" % (account,)

if __name__ == "__main__":
    generate()
