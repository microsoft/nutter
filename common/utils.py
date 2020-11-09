"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

def recursive_find(dict_instance, keys):
    if not isinstance(keys, list):
        raise ValueError("Expected list of keys")
    if not isinstance(dict_instance, dict):
        return None
    if len(keys) == 0:
        return None
    key = keys[0]
    value = dict_instance.get(key, None)
    if value is None:
        return None
    if len(keys) == 1:
        return value
    return recursive_find(value, keys[1:len(keys)])

def contains_test_prefix_or_surfix(name):
    if name is None:
        return False

    return name.lower().startswith('test_') or name.lower().endswith('_test')
