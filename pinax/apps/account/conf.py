from __future__ import absolute_import, unicode_literals
from django.conf import settings

REQUIRED_EMAIL = getattr(settings, "ACCOUNT_REQUIRED_EMAIL", False)
EMAIL_VERIFICATION = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", False)
EMAIL_VERIFICATION_PASSWORD_RESET = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION_PASSWORD_RESET", False)
EMAIL_AUTHENTICATION = getattr(settings, "ACCOUNT_EMAIL_AUTHENTICATION", False)
UNIQUE_EMAIL = getattr(settings, "ACCOUNT_UNIQUE_EMAIL", False)
