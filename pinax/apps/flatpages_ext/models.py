# TODO: authority, markup, markup-form
from django.contrib.flatpages.models import FlatPage
import versioning

versioning.register(FlatPage, ['title', 'content', 'template_name', ])
