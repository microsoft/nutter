"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import common.testresult as testresult
from common.apiclientresults import ExecuteNotebookResult
from cli.resultsvalidator import ExecutionResultsValidator, TestCaseFailureException, JobExecutionFailureException, NotebookExecutionFailureException, InvalidNotebookOutputException
import json


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
    data_json = """
                {"notebook_output":
                {"result": "IHaveReturned", "truncated": false},
                "metadata":
                {"execution_duration": 15000,
                "run_type": "SUBMIT_RUN",
                "cleanup_duration": 0,
                "number_in_job": 1,
                "cluster_instance":
                {"cluster_id": "0925-141d1222-narcs242",
                "spark_context_id": "803963628344534476"},
                "creator_user_name": "abc@microsoft.com",
                "task": {"notebook_task": {"notebook_path": "/test_mynotebook"}},
                "run_id": 7, "start_time": 1569887259173,
                "job_id": 4,
                "state": {"result_state": "SUCCESS", "state_message": "",
                "life_cycle_state": "TERMINATED"}, "setup_duration": 2000,
                "run_page_url": "https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1",
                "cluster_spec": {"existing_cluster_id": "0925-141122-narcs242"}, "run_name": "myrun"}}
                """
    data_dict = json.loads(data_json)
    data_dict['notebook_output']['result'] = notebook_result
    data_dict['metadata']['state']['result_state'] = result_state
    data_dict['metadata']['state']['life_cycle_state'] = life_cycle_state

    return ExecuteNotebookResult.from_job_output(data_dict)
