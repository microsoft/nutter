"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import base64

import mock
import pytest
from common.testresult import TestResult, TestResults
from py4j.protocol import Py4JError, Py4JJavaError


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


def test__deserialize__empty_data__throws_exception():
    # Arrange
    test_results = TestResults()

    invalid_data = ""

    # Act / Assert
    with pytest.raises(Exception):
        test_results.deserialize(invalid_data)


def test__deserialize__invalid_pickle_data__throws_exception():
    # Arrange
    test_results = TestResults()

    invalid_data = "test"

    # Act / Assert
    with pytest.raises(Exception):
        test_results.deserialize(invalid_data)


def test__deserialize__py4j_javaerror__is_serializable_and_deserializable():
    # Arrange
    test_results = TestResults()

    py4j_exception = get_mock_py4j_error_exception(get_mock_gateway_client(), mock_target_id="o123")

    test_results.append(TestResult("Test Name", True, 1, [], py4j_exception))

    with mock.patch('py4j.protocol.get_return_value') as mock_get_return_value:
        mock_get_return_value.return_value = 'foo'
        serialized_data = test_results.serialize()
        deserialized_data = TestResults().deserialize(serialized_data)

    assert test_results == deserialized_data


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


def get_mock_gateway_client():
    mock_client = mock.Mock()
    mock_client.send_command.return_value = "0"
    mock_client.converters = []
    mock_client.is_connected.return_value = True
    mock_client.deque = mock.Mock()
    return mock_client


def get_mock_java_object(mock_client, mock_target_id):
    mock_java_object = mock.Mock()
    mock_java_object._target_id = mock_target_id
    mock_java_object._gateway_client = mock_client
    return mock_java_object


def get_mock_py4j_error_exception(mock_client, mock_target_id):
    mock_java_object = get_mock_java_object(mock_client, mock_target_id)
    mock_errmsg = "An error occurred while calling {}.load.".format(mock_target_id)
    return Py4JJavaError(mock_errmsg, java_exception=mock_java_object)
