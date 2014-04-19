from __future__ import absolute_import, unicode_literals
# -*- coding: utf-8 -*-
import re

from django import template
from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from ..models import Post

register = template.Library()


@register.inclusion_tag("blog/blog_item.html")
def show_blog_post(blog_post):
    return {"blog_post": blog_post}


@register.assignment_tag
def user_blog_posts(user):
    return Post.objects.filter(
        author=user,
        status=2,
        language=get_language()
    ).order_by("-publish")
