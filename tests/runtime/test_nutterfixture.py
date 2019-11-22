"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from runtime.nutterfixture import NutterFixture, tag, InvalidTestFixtureException
from runtime.testcase import TestCase
from common.testresult  import TestResult, TestResults
from tests.runtime.testnutterfixturebuilder import TestNutterFixtureBuilder
from common.apiclientresults import ExecuteNotebookResult
import sys

def test__ctor__creates_fixture_loader():
    # Arrange / Act
    fix = SimpleTestFixture()

    # Assert
    assert fix.data_loader is not None

def test__execute_tests__calls_load_fixture_on_fixture_loader(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')

    # Act
    fix.execute_tests()

    # Assert
    fix.data_loader.load_fixture.assert_called_once_with(fix)

def test__execute_tests__data_loader_returns_none__throws_invalidfixtureexception(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = None

    # Act / Assert
    with pytest.raises(InvalidTestFixtureException):
        fix.execute_tests()

def test__execute_tests__data_loader_returns_empty_dictionary__returns_empty_results(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = {}

    # Act
    test_exec_results = fix.execute_tests()

    # Assert
    assert len(test_exec_results.test_results.results) == 0

def test__execute_tests__before_all_set_and_data_loader_returns_empty_dictionary__does_not_call_before_all(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = {}
    fix.before_all = lambda self: 1 == 1

    mocker.patch.object(fix, 'before_all')

    # Act
    test_results = fix.execute_tests()

    # Assert
    fix.before_all.assert_not_called()

def test__execute_tests__before_all_none_and_data_loader_returns_empty_dictionary__does_not_call_before_all(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = {}
    fix.before_all = None

    mocker.patch.object(fix, 'before_all')

    # Act
    test_results = fix.execute_tests()

    # Assert
    fix.before_all.assert_not_called()

def test__execute_tests__before_all_set_and_data_loader_returns_dictionary_with_testcases__calls_before_all(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')

    tc = __get_test_case("TestName", fix.run_test, fix.assertion_test)
    fix.before_all = lambda self: 1 == 1
    mocker.patch.object(fix, 'before_all')

    test_case_dict = {
        "test": tc
        }

    fix.data_loader.load_fixture.return_value = test_case_dict

    # Act 
    fix.execute_tests()

    # Assert
    fix.before_all.assert_called_once_with()

def test__execute_tests__after_all_set_and_data_loader_returns_empty_dictionary__does_not_call_after_all(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = {}
    fix.after_all = lambda self: 1 == 1

    mocker.patch.object(fix, 'after_all')

    # Act
    test_results = fix.execute_tests()

    # Assert
    fix.after_all.assert_not_called()

def test__execute_tests__after_all_none_and_data_loader_returns_empty_dictionary__does_not_call_after_all(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = {}
    fix.after_all = None

    mocker.patch.object(fix, 'after_all')

    # Act
    test_results = fix.execute_tests()

    # Assert
    fix.after_all.assert_not_called()

def test__execute_tests__after_all_set_and_data_loader_returns_dictionary_with_testcases__calls_after_all(mocker):
    # Arrange 
    fix = SimpleTestFixture()

    mocker.patch.object(fix.data_loader, 'load_fixture')

    tc = __get_test_case("TestName", fix.run_test, fix.assertion_test)
    fix.after_all = lambda self: 1 == 1
    mocker.patch.object(fix, 'after_all')

    test_case_dict = {
        "test": tc
        }

    fix.data_loader.load_fixture.return_value = test_case_dict

    # Act 
    fix.execute_tests()

    # Assert
    fix.after_all.assert_called_once_with()

def test__execute_tests__data_loader_returns_dictionary_with_testcases__iterates_over_dictionary_and_calls_execute(mocker):
    # Arrange 
    fix = SimpleTestFixture()
    mocker.patch.object(fix.data_loader, 'load_fixture')

    tc = __get_test_case("TestName", fix.run_test, fix.assertion_test)
    mocker.patch.object(tc, 'execute_test')
    tc.execute_test.return_value = TestResult("TestName", True, 1, [])
    tc1 = __get_test_case("TestName", fix.run_test, fix.assertion_test)
    mocker.patch.object(tc1, 'execute_test')
    tc1.execute_test.return_value = TestResult("TestName", True, 1, [])

    test_case_dict = {
        "test": tc,
        "test1": tc1
        }

    fix.data_loader.load_fixture.return_value = test_case_dict

    # Act 
    fix.execute_tests()

    # Assert
    tc.execute_test.assert_called_once_with()
    tc1.execute_test.assert_called_once_with()

def test__execute_tests__returns_test_result__calls_append_on_testresults(mocker):
    # Arrange
    fix = SimpleTestFixture()
    mocker.patch.object(fix.test_results, 'append')

    tc = __get_test_case("TestName", lambda: 1 == 1, lambda: 1 == 1)

    test_case_dict = {
        "test": tc
        }
    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = test_case_dict

    # Act 
    result = fix.execute_tests()

    # Assert 
    fix.test_results.append.assert_called_once_with(mocker.ANY)

def test__execute_tests__two_test_cases__returns_test_results_with_2_test_results(mocker):
    # Arrange
    fix = SimpleTestFixture()

    tc = __get_test_case("TestName", lambda: 1 == 1, lambda: 1 == 1)
    tc1 = __get_test_case("TestName1", lambda: 1 == 1, lambda: 1 == 1)

    test_case_dict = {
        "TestName": tc,
        "TestName1": tc1
        }

    mocker.patch.object(fix.data_loader, 'load_fixture')
    fix.data_loader.load_fixture.return_value = test_case_dict

    # Act 
    result = fix.execute_tests()

    # Assert 
    assert len(result.test_results.results) == 2


def test__run_test_method__has_list_tag_decorator__list_set_on_method():
    # Arrange
    class Wrapper(NutterFixture):
        tag_list = ["tag1", "tag2"]
        @tag(tag_list)
        def run_test(self):
            lambda: 1 == 1

    test_name = "test"
    tag_list = ["tag1", "tag2"]

    test_fixture = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .with_run(test_name, Wrapper.run_test) \
        .build()

    # Act / Assert
    assert tag_list == test_fixture.run_test.tag

def test__run_test_method__has_str_tag_decorator__str_set_on_method():
    # Arrange
    class Wrapper(NutterFixture):
        tag_str = "mytag"
        @tag(tag_str)
        def run_test(self):
            lambda: 1 == 1

    test_name = "test"
    test_fixture = TestNutterFixtureBuilder() \
        .with_name("MyClass") \
        .with_assertion(test_name) \
        .with_run(test_name, Wrapper.run_test) \
        .build()

    # Act / Assert
    assert "mytag" == test_fixture.run_test.tag
 
def test__run_test_method__has_tag_decorator_not_list__raises_value_error():
    # Arrange
    with pytest.raises(ValueError):
        class Wrapper(NutterFixture):
            tag_invalid = {}
            @tag(tag_invalid)
            def run_test(self):
                lambda: 1 == 1

def test__run_test_method__has_tag_decorator_not_listhas_invalid_tag_decorator_none__raises_value_error():
    # Arrange
    with pytest.raises(ValueError):
        class Wrapper(NutterFixture):
            tag_invalid = None
            @tag(tag_invalid)
            def run_test(self):
                lambda: 1 == 1

def test__non_run_test_method__valid_tag_on_non_run_method__raises_value_error():
    # Arrange
    with pytest.raises(ValueError):
        class Wrapper(NutterFixture):
            tag_valid = "mytag"
            @tag(tag_valid)
            def assertion_test(self):
                lambda: 1 == 1

def __get_test_case(name, setrun, setassert):
    tc = TestCase(name)
    tc.set_run(setrun)
    tc.set_assertion(setassert)

    return tc

def test__run_test_method__has_invalid_tag_decorator_not_list_or_str_using_class_not_builder__raises_value_error():
    # Arrange
    simple_test_fixture = SimpleTestFixture()

    # Act / Assert
    with pytest.raises(ValueError):
        simple_test_fixture.run_test_with_invalid_decorator()

def test__run_test_method__has_valid_tag_decorator_in_class__tag_set_on_method():
    # Arrange
    simple_test_fixture = SimpleTestFixture()

    # Act / Assert 
    assert "mytag" == simple_test_fixture.run_test_with_valid_decorator.tag

class SimpleTestFixture(NutterFixture):

    def before_test(self):
        pass

    def run_test(self):
        pass

    def assertion_test(self):
        assert 1 == 1

    def after_test(self):
        pass

    @tag("mytag")
    def run_test_with_valid_decorator(self):
        pass

    @tag
    def run_test_with_invalid_decorator(self):
        pass

