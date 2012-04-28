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


def patch_lookup_channel():
    """Patches the ajax_select.LookupChannel"""
    setattr(LookupChannel, 'get_query', get_query)

patch_lookup_channel()
