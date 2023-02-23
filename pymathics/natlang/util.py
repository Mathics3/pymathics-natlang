# -*- coding: utf-8 -*-

"""
utils
"""

# Don't consider this for user documentation
no_doc = True


def merge_dictionaries(a, b):
    c = a.copy()
    c.update(b)
    return c
