"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import os
import pytest
import time
from common.testresult  import TestResult
from runtime.nutterfixture import tag
from runtime.testcase import TestCase, NoTestCasesFoundError

def test__isvalid_rundoesntexist_returnsfalse():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    tc.set_assertion(fixture.assertion_test)

    # Act
    isvalid = tc.is_valid()

    # Assert
    assert False == isvalid 

def test__isvalid_assertiondoesntexist_returnsfalse():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    tc.set_run(fixture.run_test)

    # Act
    isvalid = tc.is_valid()

    # Assert
    assert False == isvalid

def test__isvalid_runandassertionexist_returnstrue():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    tc.set_assertion(fixture.assertion_test)
    tc.set_run(fixture.run_test)

    # Act
    isvalid = tc.is_valid()

    # Assert
    assert True == isvalid

def test__getinvalidmessage_rundoesntexist_returnsrunerrormessage():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    tc.set_assertion(fixture.assertion_test)

    expected_message = tc.ERROR_MESSAGE_RUN_MISSING 

    # Act
    invalid_message = tc.get_invalid_message()

    # Assert
    assert expected_message == invalid_message

def test__getinvalidmessage_assertiondoesntexist_returnsassertionerrormessage():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    tc.set_run(fixture.run_test)

    expected_message = tc.ERROR_MESSAGE_ASSERTION_MISSING 

    # Act
    invalid_message = tc.get_invalid_message()

    # Assert
    assert expected_message == invalid_message

def test__getinvalidmessage_runandassertiondontexist_returnsrunandassertionerrormessage():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    # Act
    invalid_message = tc.get_invalid_message()

    # Assert
    assertion_message_exists = tc.ERROR_MESSAGE_ASSERTION_MISSING in invalid_message
    run_message_exists = tc.ERROR_MESSAGE_RUN_MISSING in invalid_message

    assert assertion_message_exists == True
    assert run_message_exists == True

def test__set_run__function_passed__sets_run_function():
    # Arrange
    tc = TestCase("Test Name")
    fixture = TestFixture()
    
    # Act
    tc.set_run(fixture.run_test)

    # Assert
    assert tc.run == fixture.run_test

def test__set_assertion__function_passed__sets_assertion_function():
    # Arrange
    tc = TestCase("Test Name")
    func = lambda: 1 == 1 
    
    # Act
    tc.set_assertion(func)

    # Assert
    assert tc.assertion == func

def test__set_before__function_passed__sets_before_function():
    # Arrange
    tc = TestCase("Test Name")
    func = lambda: 1 == 1 
    
    # Act
    tc.set_before(func)

    # Assert
    assert tc.before == func

def test__set_after__function_passed__sets_after_function():
    # Arrange
    tc = TestCase("Test Name")
    func = lambda: 1 == 1 
    
    # Act
    tc.set_after(func)

    # Assert
    assert tc.after == func

def test__execute_test__before_set__calls_before(mocker):
    # Arrange
    tc = TestCase("TestName")

    tc.set_before(lambda: 1 == 1)
    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)
    mocker.patch.object(tc, 'before')

    # Act
    test_result = tc.execute_test()

    # Assert
    tc.before.assert_called_once_with()

def test__execute_test__before_not_set__does_not_call_before(mocker):
    # Arrange
    tc = TestCase("TestName")

    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)
    mocker.patch.object(tc, 'before')

    # Act
    test_result = tc.execute_test()

    # Assert
    tc.before.assert_not_called()

def test__execute_test__after_set__calls_after(mocker):
    # Arrange
    tc = TestCase("TestName")

    tc.set_after(lambda: 1 == 1)
    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)
    mocker.patch.object(tc, 'after')

    # Act
    test_result = tc.execute_test()

    # Assert
    tc.after.assert_called_once_with()

def test__execute_test__after_not_set__does_not_call_after(mocker):
    # Arrange
    tc = TestCase("TestName")

    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)
    mocker.patch.object(tc, 'after')

    # Act
    test_result = tc.execute_test()

    # Assert
    tc.after.assert_not_called()

def test__execute_test__method_in_assert_doesnt_throw__returns_pass_testresult(mocker):
    # Arrange
    tc = TestCase("TestName")
    fixture = TestFixture()

    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result == TestResult("TestName", True, None, [], None)

def test__execute_test__is_valid_equals_false__returns_fail_testresult():
    # Arrange
    tc = TestCase("TestName")
    no_test_cases_error = NoTestCasesFoundError('Both a run and an assertion are required for every test')

    ## (Note - no set_assertion - so invalid)
    tc.set_run(lambda: 1 == 1)
    
    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result == TestResult("TestName", False, 1, [], no_test_cases_error)

def test__execute_test__method_in_assert_throws__returns_fail_testresult():
    # Arrange
    tc = TestCase("TestName")
    assertion_error = AssertionError('bad assert')

    lambda_that_throws = lambda: (_ for _ in ()).throw(assertion_error)

    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda_that_throws)

    # Act
    test_result = tc.execute_test()
    # Assert
    assert test_result == TestResult("TestName", False, 1, [], assertion_error)


def test__execute_test__method_in_run_throws__returns_fail_testresult():
    # Arrange
    tc = TestCase("TestName")
    not_implemented_exception = NotImplementedError("Whatever was not implemented")

    lambda_that_throws = lambda: (_ for _ in ()).throw(not_implemented_exception)

    tc.set_run(lambda_that_throws)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result == TestResult("TestName", False, 1, [], not_implemented_exception)

def test__execute_test__method_in_before_throws__returns_fail_testresult():
    # Arrange
    tc = TestCase("TestName")
    not_implemented_exception = NotImplementedError("Whatever was not implemented")

    lambda_that_throws = lambda: (_ for _ in ()).throw(not_implemented_exception)

    tc.set_before(lambda_that_throws)
    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result == TestResult("TestName", False, 1, [], not_implemented_exception)

def test__execute_test__method_in_after_throws__returns_fail_testresult():
    # Arrange
    tc = TestCase("TestName")
    not_implemented_exception = NotImplementedError("Whatever was not implemented")

    lambda_that_throws = lambda: (_ for _ in ()).throw(not_implemented_exception)

    tc.set_after(lambda_that_throws)
    tc.set_before(lambda: 1 == 1)
    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result == TestResult("TestName", False, 1, [], not_implemented_exception)

def test__execute_test__method_throws__returns_stacktrace_in_testresult():
    # Arrange
    tc = TestCase("TestName")
    not_implemented_exception = NotImplementedError("Whatever was not implemented")

    lambda_that_throws = lambda: (_ for _ in ()).throw(not_implemented_exception)

    tc.set_run(lambda_that_throws)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result.stack_trace

def test__execute_test__no_constraints__sets_execution_time():
    # Arrange
    tc = TestCase("TestName")
    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)
    
    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result.execution_time > 0

def test__run_method__no_tags__tags_list_empty(mocker):
    # Arrange
    tc = TestCase("TestName")
    tc.set_run(lambda: 1 == 1)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert len(tc.tags) == 0

def test__run_method__string_tag__tags_list_contains_string(mocker):
    # Arrange
    strtag = "testtag"
    @tag(strtag)
    def run_TestName():
        lambda: 1 == 1

    tc = TestCase("TestName")
    tc.set_run(run_TestName)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert [strtag] == tc.tags

def test__run_method__list_tag__tags_list_contains_list(mocker):
    # Arrange
    tag_list = ["taga", "tagb"]
    @tag(tag_list)
    def run_TestName():
        lambda: 1 == 1

    tc = TestCase("TestName")
    tc.set_run(run_TestName)
    tc.set_assertion(lambda: 1 == 1)

    # Act
    test_result = tc.execute_test()

    # Assert
    assert tc.tags == tag_list

def test__execute__run_has_tag__test_results_returns_tags():
    # Arrange
    tag_list = ["taga", "tagb"]
    @tag(tag_list)
    def run_TestName():
        lambda: 1 == 1

    tc = TestCase("TestName")
    tc.set_run(run_TestName)
    tc.set_assertion(lambda: 1 == 1)
    
    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result.tags == tag_list

def test__execute__run_has_tag_and_execute_fails__test_results_returns_tags():
    # Arrange
    tag_list = ["taga", "tagb"]
    @tag(tag_list)
    def run_TestName():
        pass

    def assertion_TestName():
        assert 1 == 2
    
    tc = TestCase("TestName")
    tc.set_run(run_TestName)
    tc.set_assertion(assertion_TestName)
    
    # Act
    test_result = tc.execute_test()

    # Assert
    assert test_result.tags == tag_list

class TestFixture():

    # def before_all(self):
    #     return True
    def before_test(self):
        return True

    def run_test(self):
        return True
    def throw(self):
        raise AssertionError("Method not implemented")
    def assertion_test(self):
        return True

    def after_test(self):
        return True
    # def after_all(self):
    #     return True