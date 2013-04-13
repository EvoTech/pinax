from cache_tagging.django_cache_tagging import registry
from .models import Article


def article_invalidator(*a, **kw):
    """Returns tags for cache invalidation"""
    obj = kw['instance']
    tags = []
    tags.append('wiki.article.pk:{0}'.format(obj.pk))
    return tags

caches = [
    (Article, article_invalidator, ),
]

registry.register(caches)
