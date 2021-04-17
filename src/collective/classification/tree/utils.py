# -*- coding: utf-8 -*-

from collective.classification.tree.caching import forever_context_cache_key
from plone.memoize import ram


@ram.cache(forever_context_cache_key)
def iterate_over_tree(obj):
    """Iterate over an object to get all sub objects"""
    result = []
    for e in obj.values():
        result.append(e)
        if len(e) > 0:
            result.extend(iterate_over_tree(e))
    return result
