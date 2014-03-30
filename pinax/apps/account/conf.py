from __future__ import absolute_import, unicode_literals
import sys
from django_ext.conf import Settings

REQUIRED_EMAIL = False
EMAIL_VERIFICATION = False
EMAIL_VERIFICATION_PASSWORD_RESET = False
EMAIL_AUTHENTICATION = False
UNIQUE_EMAIL = False

settings = Settings('ACCOUNT', sys.modules[__name__])
