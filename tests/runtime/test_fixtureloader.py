"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from runtime.fixtureloader import FixtureLoader
from tests.runtime.testnutterfixturebuilder import TestNutterFixtureBuilder

def test__get_fixture_loader__returns_fixtureloader():
    # Arrange / Act
    loader = FixtureLoader()

    # Assert
    assert isinstance(loader, FixtureLoader)

def test__load_fixture__none_passed_raises__valueerror():
    # Arrange 
    loader = FixtureLoader()

    # Act
    with pytest.raises(ValueError):
        loader.load_fixture(None)
 
def test__load_fixture__one_assertion_method__adds_one_testclass_to_dictionary_with_assert_set():
    # Arrange
    test_name = "fred"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert len(loaded_fixture) == 1
    __assert_test_case_from_dict(loaded_fixture, test_name, True, True, False, True)

def test__load_fixture__one_assertion_method_one_additional_method__adds_one_testclass_to_dictionary_with_assert_set():
    # Arrange
    test_name = "fred"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .with_test(test_name) \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert len(loaded_fixture) == 1
    __assert_test_case_from_dict(loaded_fixture, test_name, True, True, False, True)

def test__load_fixture__one_assertion_one_run_method__adds_one_testclass_to_dictionary_with_assert_and_run_set():
    # Arrange
    test_name = "fred"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .with_run(test_name) \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert len(loaded_fixture) == 1
    __assert_test_case_from_dict(loaded_fixture, test_name, True, False, False, True)

def test__load_fixture__before_all__no_test_case_set_because_method_exists_on_fixture():
    # Arrange
    test_name = "fred"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .with_run(test_name) \
        .with_before_all() \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert "before_all" not in loaded_fixture
    assert "all" not in loaded_fixture

def test__load_fixture__after_all__no_test_case_set_because_method_exists_on_fixture():
    # Arrange
    test_name = "fred"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .with_run(test_name) \
        .with_after_all() \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert "after_all" not in loaded_fixture
    assert "all" not in loaded_fixture

def test__load_fixture__two_assertion_one_run_method__adds_two_testclass_to_dictionary():
    # Arrange
    test_name_1 = "fred"
    test_name_2 = "hank"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name_1) \
        .with_assertion(test_name_2) \
        .with_run(test_name_1) \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert len(loaded_fixture) == 2
    __assert_test_case_from_dict(loaded_fixture, test_name_1, True, False, False, True)
    __assert_test_case_from_dict(loaded_fixture, test_name_2, True, True, False, True)

def test__load_fixture__three_with_all_methods__adds_three_testclass_to_dictionary():
    # Arrange
    test_name_1 = "fred"
    test_name_2 = "hank"
    test_name_3 = "will"
    new_class = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_before(test_name_1) \
        .with_before(test_name_2) \
        .with_before(test_name_3) \
        .with_run(test_name_1) \
        .with_run(test_name_2) \
        .with_run(test_name_3) \
        .with_assertion(test_name_1) \
        .with_assertion(test_name_2) \
        .with_assertion(test_name_3) \
        .with_after(test_name_1) \
        .with_after(test_name_2) \
        .with_after(test_name_3) \
        .build()

    loader = FixtureLoader()

    # Act 
    loaded_fixture = loader.load_fixture(new_class())

    # Assert
    assert len(loaded_fixture) == 3
    __assert_test_case_from_dict(loaded_fixture, test_name_1, False, False, False, False)
    __assert_test_case_from_dict(loaded_fixture, test_name_2, False, False, False, False)
    __assert_test_case_from_dict(loaded_fixture, test_name_3, False, False, False, False)


def __assert_test_case_from_dict(test_case_dict, expected_name, before_none, run_none, assertion_none, after_none):
    assert expected_name in test_case_dict

    test_case = test_case_dict[expected_name]
    assert (test_case.before is None) == before_none
    assert (test_case.run is None) == run_none
    assert (test_case.assertion is None) == assertion_none
    assert (test_case.after is None) == after_none

  


