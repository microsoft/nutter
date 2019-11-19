"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from common.testexecresults import TestExecResults
from common.testresult import TestResults, TestResult

def test__ctor__test_results_not_correct_type__raises_type_error():
    with pytest.raises(TypeError):
        test_exec_result = TestExecResults("invalidtype")

def test__to_string__valid_test_results__creates_view_from_test_results_and_returns(mocker):
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("test1", True, 10, []))
    test_results.append(TestResult("test2", True, 10, []))

    test_exec_result = TestExecResults(test_results)

    mocker.patch.object(test_exec_result, 'get_ExecuteNotebookResult')
    notebook_result = TestExecResults(test_results).get_ExecuteNotebookResult("", test_results)
    test_exec_result.get_ExecuteNotebookResult.return_value = notebook_result

    mocker.patch.object(test_exec_result.runcommand_results_view, 'add_exec_result')
    mocker.patch.object(test_exec_result.runcommand_results_view, 'get_view')
    test_exec_result.runcommand_results_view.get_view.return_value = "expectedview"
    
    # Act
    view = test_exec_result.to_string()

    # Assert
    test_exec_result.get_ExecuteNotebookResult.assert_called_once_with("", test_results)
    test_exec_result.runcommand_results_view.add_exec_result.assert_called_once_with(notebook_result)
    test_exec_result.runcommand_results_view.get_view.assert_called_once_with()
    assert view == "expectedview"

def test__to_string__valid_test_results_run_from_notebook__creates_view_from_test_results_and_returns(mocker):
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("test1", True, 10, []))
    test_results.append(TestResult("test2", True, 10, []))

    test_exec_result = TestExecResults(test_results)

    # Act
    view = test_exec_result.to_string()

    # Assert
    assert "PASSING TESTS" in view
    assert "test1" in view
    assert "test2" in view

def test__exit__valid_test_results__serializes_test_results_and_passes_to_dbutils_exit(mocker):
    # Arrange
    test_results = TestResults()
    test_results.append(TestResult("test1", True, 10, []))
    test_results.append(TestResult("test2", True, 10, []))

    test_exec_result = TestExecResults(test_results)

    mocker.patch.object(test_results, 'serialize')
    serialized_data = "serializeddata"
    test_results.serialize.return_value = serialized_data

    dbutils_stub = DbUtilsStub()

    # Act
    test_exec_result.exit(dbutils_stub)

    # Assert
    test_results.serialize.assert_called_with()
    assert True == dbutils_stub.notebook.exit_called
    assert serialized_data == dbutils_stub.notebook.data_passed

class DbUtilsStub:
    def __init__(self):
        self.notebook = NotebookStub()

class NotebookStub():
    def __init__(self):
        self.exit_called = False
        self.data_passed = ""

    def exit(self, data):
        self.exit_called = True
        self.data_passed = data