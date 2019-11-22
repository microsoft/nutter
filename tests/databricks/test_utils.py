"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import common.utils as utils


def test__recursive_find__2_levels_value__value(mocker):
    keys = ["a", "b"]
    test_dict = __get_test_dict()
    value = utils.recursive_find(test_dict, keys)

    assert value == "c"


def test__recursive_find__3_levels_no_value__none(mocker):
    keys = ["a", "b", "c"]
    test_dict = __get_test_dict()
    value = utils.recursive_find(test_dict, keys)

    assert value is None


def test__recursive_find__3_levels_value__value(mocker):
    keys = ["a", "C", "D"]
    test_dict = __get_test_dict()
    value = utils.recursive_find(test_dict, keys)

    assert value == "E"


def test__recursive_find__3_levels_value__value(mocker):
    keys = ["a", "C", "D"]
    test_dict = __get_test_dict()
    value = utils.recursive_find(test_dict, keys)

    assert value == "E"


def test__recursive_find__2_levels_dict__dict(mocker):
    keys = ["a", "C"]
    test_dict = __get_test_dict()
    value = utils.recursive_find(test_dict, keys)

    assert isinstance(value, dict)


def __get_test_dict():
    test_dict = {"a": {"b": "c", "C": {"D": "E"}}, "1": {"2": {"3": "4"}}}

    return test_dict
