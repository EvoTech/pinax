from django.core.exceptions import PermissionDenied
from ajax_select import LookupChannel


def get_query(self,q,request):
    """ return a query set searching for the query string q 
        either implement this method yourself or set the search_field
        in the LookupChannel class definition
    """
    try:
        limit = int(request.GET["limit"])
    except (KeyError, ValueError):
        limit = 10

    if limit > 100:
        limit = 100
    kwargs = { "%s__icontains" % self.search_field : q }
    return self.model.objects.filter(**kwargs).order_by(self.search_field)[:limit]


def check_auth(self,request):
    """ to ensure that nobody can get your data via json simply by knowing the URL.
        public facing forms should write a custom LookupChannel to implement as you wish.
        also you could choose to return HttpResponseForbidden("who are you?")
        instead of raising PermissionDenied (401 response)
    """
    if not request.user.is_authenticated():
        raise PermissionDenied


def patch_lookup_channel():
    """Patches the ajax_select.LookupChannel"""
    setattr(LookupChannel, 'get_query', get_query)
    setattr(LookupChannel, 'check_auth', check_auth)

patch_lookup_channel()
