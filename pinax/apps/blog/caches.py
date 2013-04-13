from cache_tagging.django_cache_tagging import registry
from .models import Post


def blog_invalidator(*a, **kw):
    """Returns tags for cache invalidation"""
    obj = kw['instance']
    tags = []
    tags.append('blog.post.pk:{0}'.format(obj.pk))
    return tags

caches = [
    (Post, blog_invalidator, ),
]

registry.register(caches)
