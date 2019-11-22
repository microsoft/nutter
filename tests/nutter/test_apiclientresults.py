"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import json
from common.api import Nutter, TestNotebook, NutterStatusEvents
import common.api as nutter_api
from common.testresult import TestResults, TestResult
from common.apiclientresults import ExecuteNotebookResult, NotebookOutputResult

def test__is_any_error__not_terminated__true():
    exec_result = _get_run_test_response('', 'SKIPPED','')

    assert exec_result.is_any_error


def test__is_any_error__terminated_not_success__true():
    exec_result = _get_run_test_response('FAILED', 'TERMINATED','')

    assert exec_result.is_any_error


def test__is_any_error__terminated_success_invalid_results__true():
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED','')

    assert exec_result.is_any_error


def test__is_any_error__terminated_success_valid_results_with_failure__true():
    test_results = TestResults()
    test_results.append(TestResult('case',False, 10,[]))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED',test_results.serialize())

    assert exec_result.is_any_error



def test__is_any_error__terminated_success_valid_results_with_no_failure__false():
    test_results = TestResults()
    test_results.append(TestResult('case',True, 10,[]))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED',test_results.serialize())

    assert not exec_result.is_any_error



def test__is_any_error__terminated_success_2_valid_results_with_no_failure__false():
    test_results = TestResults()
    test_results.append(TestResult('case',True, 10,[]))
    test_results.append(TestResult('case2',True, 10,[]))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED',test_results.serialize())

    assert not exec_result.is_any_error

def test__is_any_error__terminated_success_2_results_1_invalid__true():
    test_results = TestResults()
    test_results.append(TestResult('case',True, 10,[]))
    test_results.append(TestResult('case2',False, 10,[]))
    exec_result = _get_run_test_response('SUCCESS', 'TERMINATED',test_results.serialize())

    assert exec_result.is_any_error

def test__is_run_from_notebook__result_state_NA__returns_true():
    # Arrange
    nbr = NotebookOutputResult('N/A', None, None)

    # Act
    is_run_from_notebook = nbr.is_run_from_notebook

    #Assert
    assert True == is_run_from_notebook

def test__is_error__is_run_from_notebook_true__returns_false():
    # Arrange
    nbr = NotebookOutputResult('N/A', None, None)

    # Act
    is_error = nbr.is_error

    #Assert
    assert False == is_error

def _get_run_test_response(result_state, life_cycle_state, notebook_result):
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

