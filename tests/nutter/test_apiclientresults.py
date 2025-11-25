"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from unittest.mock import Mock
from databricks.sdk.service.jobs import Run, RunTask, NotebookTask, RunState, \
    RunLifeCycleState, RunResultState, RunOutput, NotebookOutput

from common.api import Nutter, TestNotebook, NutterStatusEvents
import common.api as nutter_api
from common.testresult import TestResults, TestResult
from common.apiclientresults import ExecuteNotebookResult, NotebookOutputResult


def test__is_any_error__not_terminated__true():
    exec_result = _get_run_test_response('', 'SKIPPED', '')

    assert exec_result.is_any_error


def test__is_any_error__terminated_not_success__true():
    exec_result = _get_run_test_response('FAILED', 'TERMINATED', '')

    assert exec_result.is_any_error


def test__is_any_error__terminated_success_invalid_results__true():
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED', '')

    assert exec_result.is_any_error


def test__is_any_error__terminated_success_valid_results_with_failure__true():
    test_results = TestResults()
    test_results.append(TestResult('case', False, 10, []))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED', test_results.serialize())

    assert exec_result.is_any_error


def test__is_any_error__terminated_success_valid_results_with_no_failure__false():
    test_results = TestResults()
    test_results.append(TestResult('case', True, 10, []))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED', test_results.serialize())

    assert not exec_result.is_any_error


def test__is_any_error__terminated_success_2_valid_results_with_no_failure__false():
    test_results = TestResults()
    test_results.append(TestResult('case', True, 10, []))
    test_results.append(TestResult('case2', True, 10, []))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED', test_results.serialize())

    assert not exec_result.is_any_error


def test__is_any_error__terminated_success_2_results_1_invalid__true():
    test_results = TestResults()
    test_results.append(TestResult('case', True, 10, []))
    test_results.append(TestResult('case2', False, 10, []))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED', test_results.serialize())

    assert exec_result.is_any_error


def test__is_run_from_notebook__result_state_NA__returns_true():
    # Arrange
    nbr = NotebookOutputResult('N/A', None, None)

    # Act
    is_run_from_notebook = nbr.is_run_from_notebook

    # Assert
    assert True == is_run_from_notebook


def test__is_error__is_run_from_notebook_true__returns_false():
    # Arrange
    nbr = NotebookOutputResult('N/A', None, None)

    # Act
    is_error = nbr.is_error

    # Assert
    assert False == is_error


def _get_run_test_response(result_state, life_cycle_state, notebook_result):
    # Create proper SDK objects instead of JSON
    result_state_enum = getattr(RunResultState, result_state) if result_state else None
    lifecycle_state_enum = getattr(RunLifeCycleState, life_cycle_state)
    
    run_info = Run(
        tasks=[
            RunTask(
                task_key="test_task",
                notebook_task=NotebookTask(notebook_path="/test_mynotebook"),
                run_id=2,
                state=RunState(
                    life_cycle_state=lifecycle_state_enum,
                    result_state=result_state_enum,
                    state_message=""
                )
            )
        ],
        run_id=1,
        run_page_url="https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1",
        state=RunState(
            life_cycle_state=lifecycle_state_enum,
            result_state=result_state_enum,
            state_message=""
        ),
    )
    
    # Create mock WorkspaceClient
    mock_client = Mock()
    mock_client.jobs.get_run_output.return_value = RunOutput(
        notebook_output=NotebookOutput(result=notebook_result, truncated=False)
    )
    
    return ExecuteNotebookResult.from_job_output(run_info, mock_client)
