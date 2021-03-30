# -*- coding: utf-8 -*-


def iterate_over_tree(obj):
    """Iterate over an object to get all sub objects"""
    result = []
    for e in obj.values():
        result.append(e)
        if len(e) > 0:
            result.extend(iterate_over_tree(e))
    return result
