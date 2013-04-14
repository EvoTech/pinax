from cache_tagging.django_cache_tagging import registry
from .models import Topic


def topic_invalidator(*a, **kw):
    """Returns tags for cache invalidation"""
    obj = kw['instance']
    tags = []
    tags.append('topics.topic.pk:{0}'.format(obj.pk))
    return tags

caches = [
    (Topic, topic_invalidator, ),
]

registry.register(caches)
