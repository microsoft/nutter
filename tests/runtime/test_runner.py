"""
Copyright (c) Microsoft Corporation.

Licensed under the MIT license.
"""

import time

import pytest

from runtime.nutterfixture import NutterFixture
from runtime.runner import NutterFixtureParallelRunner

test_cases = [
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (3, 1),
    (3, 2),
    (3, 3)
]

@pytest.mark.parametrize('num_of_tests, num_of_workers', test_cases)
def test__execute_tests__x_tests_x_workers__results_ok(num_of_tests, num_of_workers):
    # Assemble list of tests
    tests = []
    for i in range(num_of_tests):
        test_case = RunnerTestFixture()
        tests.append(test_case)

    # Execute tests
    runner = NutterFixtureParallelRunner(tests, num_of_workers)
    results = runner.execute_tests()

    # Assert results
    assert len(results.test_results.results) == len(tests)
    assert results.test_results.passed() == True

def test__execute_tests__3_tests_in_sequence_with_failed_assertion__results_ok():
    # Arrange
    tests = [
        RunnerTestFixture(),
        RunnerTestFixtureFailAssert(),
        RunnerTestFixture()
    ]

    # Act
    runner = NutterFixtureParallelRunner(tests, 1)
    results = runner.execute_tests()

    # Assert
    assert len(results.test_results.results) == len(tests)
    assert results.test_results.results[0].passed == True
    assert results.test_results.results[1].passed == False
    assert results.test_results.results[2].passed == True

def test__execute_tests__3_tests_in_sequence_with_run_exception__results_ok():
    # Arrange
    tests = [
        RunnerTestFixture(),
        RunnerTestFixtureRunException(),
        RunnerTestFixture()
    ]

    # Act
    runner = NutterFixtureParallelRunner(tests, 1)
    results = runner.execute_tests()

    # Assert
    assert len(results.test_results.results) == len(tests)
    assert results.test_results.results[0].passed == True
    assert results.test_results.results[1].passed == False
    assert results.test_results.results[2].passed == True

def test__execute_tests__3_tests_in_sequence_with_exec_exception__results_ok():
    # Arrange
    tests = [
        RunnerTestFixture(),
        RunnerTestFixtureExecuteException(),
        RunnerTestFixture()
    ]

    # Act
    runner = NutterFixtureParallelRunner(tests, 1)
    results = runner.execute_tests()

    # Assert
    assert len(results.test_results.results) == len(tests) - 1
    assert results.test_results.results[0].passed == True
    assert results.test_results.results[1].passed == True

class RunnerTestFixture(NutterFixture):
    def before_test(self):
        pass

    def run_test(self):
        pass

    def assertion_test(self):
        assert 1 == 1

    def after_test(self):
        pass

class RunnerTestFixtureFailAssert(NutterFixture):
    def before_test(self):
        pass

    def run_test(self):
        pass

    def assertion_test(self):
        assert 1 != 1

    def after_test(self):
        pass

class RunnerTestFixtureRunException(NutterFixture):
    def before_test(self):
        pass

    def run_test(self):
        raise(Exception())

    def assertion_test(self):
        assert 1 == 1

    def after_test(self):
        pass

class RunnerTestFixtureExecuteException(NutterFixture):
    def execute_tests(self):
        raise(Exception())
