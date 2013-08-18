from __future__ import absolute_import, unicode_literals
from django.utils import translation
from pages.templatetags.pages_tags import get_page_from_string_or_id


def get_page_url(page, lang=None):
    """Returns url for page from django-page-cms"""
    if lang is None:
        lang = translation.get_language()
    page = get_page_from_string_or_id(page, lang)
    if not page:
        return ''
    url = page.get_url_path(language=lang)
    return url or ''
