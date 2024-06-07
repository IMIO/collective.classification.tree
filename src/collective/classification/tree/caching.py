# -*- coding: utf-8 -*-

from plone.memoize.interfaces import ICacheChooser
from zope.component import queryUtility
from plone.memoize import ram


def forever_context_cache_key(func, context):
    """Cache key for functions where context is the single parameter"""
    return context.UID()


def get_cache(key):
    cache_chooser = queryUtility(ICacheChooser)
    if cache_chooser is not None:
        return cache_chooser(key)
    else:
        return ram.RAMCacheAdapter(ram.global_cache, globalkey=key)


def invalidate_cache(func, key):
    cache = get_cache(key)
    if not isinstance(cache, ram.RAMCacheAdapter):
        raise NotImplementedError("Can not invalidate for cache class {0}".format(str(cache.__class__)))
    key = dict(key=cache._make_key("{0}:{1}".format(func, key)))
    cache.ramcache.invalidate(func, key=key)
