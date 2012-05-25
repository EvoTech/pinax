

class UserNotLazyMiddleware:
    """User is not lasy, for resolving some problems with notifications.

    Temporary fix for django bug: "can't pickle function objects"
    https://code.djangoproject.com/ticket/16563
    """
    def process_request(self, request):
        """Process request handler"""
        try:
            from django.contrib.auth.middleware import get_user
            request.user = get_user(request)
        except:
            pass
