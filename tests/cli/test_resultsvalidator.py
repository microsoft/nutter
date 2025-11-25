"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from unittest.mock import Mock
from databricks.sdk.service.jobs import Run, RunTask, NotebookTask, RunState, \
    RunLifeCycleState, RunResultState, RunOutput, NotebookOutput

import common.testresult as testresult
from common.apiclientresults import ExecuteNotebookResult
from cli.resultsvalidator import ExecutionResultsValidator, TestCaseFailureException, JobExecutionFailureException, NotebookExecutionFailureException, InvalidNotebookOutputException


def test__validate__results_is_none__valueerror():
    with pytest.raises(ValueError):
        ExecutionResultsValidator().validate(None)


def test__validate__results_are_empty__no_ex():
    exec_results = []
    ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_no_testcases__no_ex():
    test_results = testresult.TestResults()
    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result]

    ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_one_testcases__no_ex():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=True, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result]

    ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_two_exec_results__no_ex():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=True, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result, exec_result]

    ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_two_testcases__no_ex():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=True, execution_time=1, tags = [])
    test_results.append(test_case)
    test_case = testresult.TestResult(
        test_name="mytest2_case", passed=True, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result]

    ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_two_testcases_one_failure__no_ex():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=True, execution_time=1, tags = [])
    test_results.append(test_case)
    test_case = testresult.TestResult(
        test_name="mytest2_case", passed=False, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result]

    with pytest.raises(TestCaseFailureException):
        ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_failed_testcase__throws_testcasefailurexception():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=False, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result]

    with pytest.raises(TestCaseFailureException):
        ExecutionResultsValidator().validate(exec_results)


def test__validate__results_have_invalid_output__throws_invalidnotebookoutputexception():

    exec_result = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', '')
    exec_results = [exec_result]

    with pytest.raises(InvalidNotebookOutputException):
        ExecutionResultsValidator().validate(exec_results)


def test__validate__results_with_notebook_failure__throws_notebookexecutionfailureexception():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=False, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'FAILED', 'TERMINATED', test_results.serialize())
    exec_results = [exec_result]

    with pytest.raises(NotebookExecutionFailureException):
        ExecutionResultsValidator().validate(exec_results)


def test__validate__results_with_job_failure__throws_jobexecutionfailureexception():
    test_results = testresult.TestResults()
    test_case = testresult.TestResult(
        test_name="mytest_case", passed=False, execution_time=1, tags = [])
    test_results.append(test_case)

    exec_result = __get_ExecuteNotebookResult(
        'FAILED', 'INTERNAL_ERROR', test_results.serialize())
    exec_results = [exec_result]

    with pytest.raises(JobExecutionFailureException):
        ExecutionResultsValidator().validate(exec_results)


def __get_ExecuteNotebookResult(result_state, life_cycle_state, notebook_result):
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
