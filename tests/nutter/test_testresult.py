"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import json
from common.testresult import TestResults, TestResult
import pickle
import base64

def test__testresults_append__type_not_testresult__throws_error():
    # Arrange
    test_results = TestResults()

    # Act/Assert
    with pytest.raises(TypeError):
        test_results.append("Test")

def test__testresults_append__type_testresult__appends_testresult():
    # Arrange
    test_results = TestResults()

    # Act
    test_results.append(TestResult("Test Name", True, 1, []))
    
    # Assert
    assert len(test_results.results) == 1

def test__eq__test_results_not_equal__are_not_equal():
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("Test NameX", True, 1, []))
    test_results.append(TestResult("Test Name1", True, 1, [], ValueError("Error")))

    test_results1 = TestResults()
    test_results1.append(TestResult("Test Name", True, 1, []))
    test_results1.append(TestResult("Test Name1", True, 1, [], ValueError("Error")))

    # Act / Assert
    are_not_equal = test_results != test_results1
    assert are_not_equal == True

def test__deserialize__no_constraints__is_serializable_and_deserializable():
    # Arrange
    test_results = TestResults()

    test_results.append(TestResult("Test Name", True, 1, []))
    test_results.append(TestResult("Test Name1", True, 1, [], ValueError("Error")))

    serialized_data = test_results.serialize()

    deserialized_data = TestResults().deserialize(serialized_data)

    assert test_results == deserialized_data

def test__deserialize__empty_pickle_data__throws_exception():
    # Arrange
    test_results = TestResults()

    invalid_pickle = ""

    # Act / Assert
    with pytest.raises(Exception):
        test_results.deserialize(invalid_pickle)

def test__deserialize__invalid_pickle_data__throws_Exception():
    # Arrange
    test_results = TestResults()

    invalid_pickle = "test"

    # Act / Assert
    with pytest.raises(Exception):
        test_results.deserialize(invalid_pickle)


def test__eq__test_results_equal_but_not_same_ref__are_equal():
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("Test Name", True, 1, []))
    test_results.append(TestResult("Test Name1", True, 1, [], ValueError("Error")))

    test_results1 = TestResults()
    test_results1.append(TestResult("Test Name", True, 1, []))
    test_results1.append(TestResult("Test Name1", True, 1, [], ValueError("Error")))

    # Act / Assert
    assert test_results == test_results1

def test__num_tests__5_test_cases__is_5():
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("Test Name", True, 1, []))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))

    # Act / Assert
    assert 5 == test_results.test_cases

def test__num_failures__5_test_cases_4_failures__is_4():
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("Test Name", True, 1, []))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 1, [], ValueError("Error")))

    # Act / Assert
    assert 4 == test_results.num_failures

def test__total_execution_time__5_test_cases__is_sum_of_execution_times():
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("Test Name", True, 1.12, []))
    test_results.append(TestResult("Test Name1", False, 1.0005, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 10.000034, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 7.66, [], ValueError("Error")))
    test_results.append(TestResult("Test Name1", False, 13.21, [], ValueError("Error")))

    # Act / Assert
    assert 32.990534 == test_results.total_execution_time

def test__serialize__result_data__is_base64_str():
    test_results = TestResults()
    serialized_data = test_results.serialize()
    serialized_bin_data = base64.encodebytes(pickle.dumps(test_results))
    
    assert serialized_data == str(serialized_bin_data, "utf-8")


def test__deserialize__data_is_base64_str__can_deserialize():
    test_results = TestResults()
    serialized_bin_data =  pickle.dumps(test_results)
    serialized_str = str(base64.encodebytes(serialized_bin_data), "utf-8")
    test_results_from_data = TestResults().deserialize(serialized_str)

    assert test_results == test_results_from_data
