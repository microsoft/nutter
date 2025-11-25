"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import os

__version__ = '0.2.0'

BUILD_NUMBER_ENV_VAR = 'NUTTER_BUILD_NUMBER'


def get_nutter_version():
    build_number = os.environ.get(BUILD_NUMBER_ENV_VAR)
    if build_number:
        return f'{__version__}.{build_number}'
    return __version__


def contains_test_prefix_or_suffix(name):
    if name is None:
        return False

    lower_name = name.lower()
    return lower_name.startswith('test_') or lower_name.endswith('_test')
