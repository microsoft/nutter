"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import sys
import pytest
from runtime.nutterfixture import NutterFixture, tag
from common.testresult  import TestResult
from tests.runtime.testnutterfixturebuilder import TestNutterFixtureBuilder


def test__execute_tests__two_valid_cases__returns_test_results_with_2_passed_test_results():
    # Arrange
    test_name_1 = "fred"
    test_name_2 = "hank"
    test_fixture = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_before(test_name_1) \
        .with_before(test_name_2) \
        .with_run(test_name_1) \
        .with_run(test_name_2) \
        .with_assertion(test_name_1) \
        .with_assertion(test_name_2) \
        .with_after(test_name_1) \
        .with_after(test_name_2) \
        .build()

    expected_result1 = TestResult(test_name_1, True, 1, [])
    expected_result2 = TestResult(test_name_2, True, 1, [])

    # Act 
    result = test_fixture().execute_tests().test_results

    # Assert 
    assert len(result.results) == 2
    assert __item_in_list_equalto(result.results, expected_result1)
    assert __item_in_list_equalto(result.results, expected_result2)

def test__execute_tests__one_valid_one_invalid__returns_correct_test_results():
    # Arrange
    test_name_1 = "shouldpass"
    test_name_2 = "shouldfail"
    fail_func = AssertionHelper().assertion_fails

    test_fixture = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_before(test_name_1) \
        .with_before(test_name_2) \
        .with_run(test_name_1) \
        .with_run(test_name_2) \
        .with_assertion(test_name_1) \
        .with_assertion(test_name_2, fail_func) \
        .with_after(test_name_1) \
        .with_after(test_name_2) \
        .build()

    expected_result1 = TestResult(test_name_1, True, 1, [])
    expected_result2 = TestResult(test_name_2, False, 1, [], AssertionError("assert 1 == 2"))

    # Act 
    result = test_fixture().execute_tests().test_results

    # Assert 
    assert len(result.results) == 2
    assert __item_in_list_equalto(result.results, expected_result1)
    assert __item_in_list_equalto(result.results, expected_result2)

def test__execute_tests__one_run_throws__returns_one_failed_testresult():
    # Arrange
    test_name_1 = "shouldthrow"
    fail_func = AssertionHelper().function_throws

    test_fixture = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_before(test_name_1) \
        .with_run(test_name_1, fail_func) \
        .with_assertion(test_name_1) \
        .with_after(test_name_1) \
        .build()

    expected_result1 = TestResult(test_name_1, False, 1, [], ValueError())
 
    # Act 
    result = test_fixture().execute_tests().test_results

    # Assert 
    assert len(result.results) == 1
    assert __item_in_list_equalto(result.results, expected_result1)

def test__execute_tests__one_has_tags_one_does_not__returns_tags_in_testresult():
    # Arrange
    class Wrapper(NutterFixture):
        tag_list = ["taga", "tagb"]
        @tag(tag_list)
        def run_test_name(self):
            lambda: 1 == 1

    test_name_1 = "test_name"
    test_name_2 = "test_name2"

    test_fixture = TestNutterFixtureBuilder() \
        .with_name(test_name_1) \
        .with_run(test_name_1, Wrapper.run_test_name) \
        .with_assertion(test_name_1) \
        .with_after(test_name_1) \
        .with_name(test_name_2) \
        .with_run(test_name_2) \
        .with_assertion(test_name_2) \
        .with_after(test_name_2) \
        .build()

    # Act 
    result = test_fixture().execute_tests().test_results

    # Assert 
    assert len(result.results) == 2
    for res in result.results:
        if res.test_name == test_name_1:
            assert ("taga" in res.tags) == True
            assert ("tagb" in res.tags) == True
        if res.test_name == test_name_2:
            assert len(res.tags) == 0

def test__execute_tests__one_test_case_with_all_methods__all_methods_called(mocker):
    # Arrange
    test_name_1 = "test"
    
    test_fixture = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_before_all() \
        .with_before(test_name_1) \
        .with_run(test_name_1) \
        .with_assertion(test_name_1) \
        .with_after(test_name_1) \
        .with_after_all() \
        .build()

    mocker.patch.object(test_fixture, 'before_all')
    mocker.patch.object(test_fixture, 'before_test')
    mocker.patch.object(test_fixture, 'run_test')
    mocker.patch.object(test_fixture, 'assertion_test')
    mocker.patch.object(test_fixture, 'after_test')
    mocker.patch.object(test_fixture, 'after_all')

    # Act 
    result = test_fixture().execute_tests()

    # Assert
    test_fixture.before_all.assert_called_once_with()
    test_fixture.before_test.assert_called_once_with()
    test_fixture.run_test.assert_called_once_with()
    test_fixture.assertion_test.assert_called_once_with()
    test_fixture.after_test.assert_called_once_with()
    test_fixture.after_all.assert_called_once_with()

def __item_in_list_equalto(list, expected_item):
    for item in list:
        if (item == expected_item):
            return True
    
    return False
    
class AssertionHelper():
    def assertion_fails(self):
        assert 1 == 2
    def function_throws(self):
        raise ValueError()

