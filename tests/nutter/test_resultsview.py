"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from unittest.mock import Mock
from databricks.sdk.service.jobs import Run, RunTask, NotebookTask, RunState, \
    RunLifeCycleState, RunResultState, RunOutput, NotebookOutput

from common.resultsview import RunCommandResultsView, TestCaseResultView, ListCommandResultView, \
    ListCommandResultsView
from common.apiclientresults import ExecuteNotebookResult
from common.testresult import TestResults, TestResult
from common.api import TestNotebook


def test__add_exec_result__vaid_instance__isadded(mocker):
    test_results = TestResults().serialize()
    notebook_results = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results)

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    assert run_results_view.total == 1


def test__add_exec_result__vaid_instance_invalid_output__isadded(mocker):
    test_results = "NO PICKLE"
    notebook_results = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results)

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    assert run_results_view.total == 1

    run_result_view = run_results_view.run_results[0]

    assert len(run_result_view.test_cases_views) == 0


def test__add_exec_result__vaid_instance_invalid_output__no_test_case_view(mocker):
    test_results = "NO PICKLE"
    notebook_results = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results)

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    assert run_results_view.total == 1


def test__add_exec_result__vaid_instance__test_case_view(mocker):
    test_results = TestResults()
    test_case = TestResult("mycase", True, 10, [])
    test_results.append(test_case)

    notebook_results = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    assert run_results_view.total == 1

    run_result_view = run_results_view.run_results[0]

    assert len(run_result_view.test_cases_views) == 1

    tc_result_view = run_result_view.test_cases_views[0]

    assert tc_result_view.test_case == test_case.test_name
    assert tc_result_view.passed == test_case.passed
    assert tc_result_view.execution_time == test_case.execution_time


def test__add_exec_result__vaid_instance_two_test_cases__two_test_case_view(mocker):
    test_results = TestResults()
    test_case = TestResult("mycase", True, 10, [])
    test_results.append(test_case)
    test_case = TestResult("mycase2", True, 10, [])
    test_results.append(test_case)

    notebook_results = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', test_results.serialize())

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    assert run_results_view.total == 1

    run_result_view = run_results_view.run_results[0]

    assert len(run_result_view.test_cases_views) == 2


def test__get_view__for_testcase_passed__returns_correct_string(mocker):
    # Arrange
    test_case = TestResult("mycase", True, 10, [])
    test_case_result_view = TestCaseResultView(test_case)

    expected_view = "mycase (10 seconds)\n"

    # Act
    view = test_case_result_view.get_view()

    # Assert
    assert expected_view == view


def test__get_view__for_testcase_failed__returns_correct_string(mocker):
    # Arrange
    stack_trace = "Stack Trace"
    exception = AssertionError("1 == 2")
    test_case = TestResult("mycase", False, 5.43, [
        'tag1', 'tag2'], exception, stack_trace)
    test_case_result_view = TestCaseResultView(test_case)

    expected_view = "mycase (5.43 seconds)\n\n" + \
                    stack_trace + "\n\n" + "AssertionError: 1 == 2" + "\n"

    # Act
    view = test_case_result_view.get_view()

    # Assert
    assert expected_view == view


def test__get_view__for_run_command_result_with_passing_test_case__shows_test_result_under_passing(
        mocker):
    test_results = TestResults()
    test_case = TestResult("mycase", True, 10, [])
    test_results.append(test_case)
    test_case_result_view = TestCaseResultView(test_case)
    serialized_results = test_results.serialize()

    notebook_results = __get_ExecuteNotebookResult(
        'SUCCESS', 'TERMINATED', serialized_results)

    # expected_view = 'Name:            \t/test_mynotebook\nNotebook Exec Result:\tTERMINATED \nTests Cases:\nCase:\tmycase\n\n\tPASSED\n\t\n\t\n\tDuration: 10\n\nCase:\tmycase2\n\n\tPASSED\n\t\n\t\n\tDuration: 10\n\n\n----------------------------------------\n'
    expected_view = '\nNotebook: /test_mynotebook - Lifecycle State: TERMINATED, Result: SUCCESS\n'
    expected_view += 'Run Page URL: {}\n'.format(notebook_results.notebook_run_page_url)
    expected_view += '============================================================\n'
    expected_view += 'PASSING TESTS\n'
    expected_view += '------------------------------------------------------------\n'
    expected_view += test_case_result_view.get_view()
    expected_view += '\n\n'
    expected_view += '============================================================\n'

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    view = run_results_view.get_view()

    assert expected_view == view


def test__get_view__for_run_command_result_with_failing_test_case__shows_test_result_under_failing(
        mocker):
    test_results = TestResults()

    stack_trace = "Stack Trace"
    exception = AssertionError("1 == 2")
    test_case = TestResult("mycase", False, 5.43, [
        'tag1', 'tag2'], exception, stack_trace)
    test_case_result_view = TestCaseResultView(test_case)
    test_results.append(test_case)

    passing_test_case1 = TestResult("mycase1", True, 10, [])
    test_results.append(passing_test_case1)
    passing_test_case_result_view1 = TestCaseResultView(passing_test_case1)

    passing_test_case2 = TestResult("mycase2", True, 10, [])
    test_results.append(passing_test_case2)
    passing_test_case_result_view2 = TestCaseResultView(passing_test_case2)

    serialized_results = test_results.serialize()

    notebook_results = __get_ExecuteNotebookResult(
        'FAILED', 'TERMINATED', serialized_results)

    expected_view = '\nNotebook: /test_mynotebook - Lifecycle State: TERMINATED, Result: FAILED\n'
    expected_view += 'Run Page URL: {}\n'.format(notebook_results.notebook_run_page_url)
    expected_view += '============================================================\n'
    expected_view += 'FAILING TESTS\n'
    expected_view += '------------------------------------------------------------\n'
    expected_view += test_case_result_view.get_view()
    expected_view += '\n\n'
    expected_view += 'PASSING TESTS\n'
    expected_view += '------------------------------------------------------------\n'
    expected_view += passing_test_case_result_view1.get_view()
    expected_view += passing_test_case_result_view2.get_view()
    expected_view += '\n\n'
    expected_view += '============================================================\n'

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    view = run_results_view.get_view()

    assert expected_view == view


def test__get_view__for_list_command__with_tests_Found__shows_listing(mocker):
    test_notebook1 = TestNotebook('test_one', '/test_one')
    test_notebook2 = TestNotebook('test_two', '/test_two')
    test_notebooks = [test_notebook1, test_notebook2]
    list_result_view1 = ListCommandResultView.from_test_notebook(test_notebook1)
    list_result_view2 = ListCommandResultView.from_test_notebook(test_notebook2)

    expected_view = '\nTests Found\n'
    expected_view += '-------------------------------------------------------\n'
    expected_view += list_result_view1.get_view()
    expected_view += list_result_view2.get_view()
    expected_view += '-------------------------------------------------------\n'

    list_results_view = ListCommandResultsView(test_notebooks)

    view = list_results_view.get_view()

    assert view == expected_view


def test__get_view__for_run_command_result_with_one_passing_one_failing__shows_failing_then_passing(
        mocker):
    stack_trace = "Stack Trace"
    exception = AssertionError("1 == 2")
    test_case = TestResult("mycase", False, 5.43, [
        'tag1', 'tag2'], exception, stack_trace)
    test_case_result_view = TestCaseResultView(test_case)

    test_results = TestResults()
    test_results.append(test_case)
    serialized_results = test_results.serialize()

    notebook_results = __get_ExecuteNotebookResult(
        'FAILED', 'TERMINATED', serialized_results)

    expected_view = '\nNotebook: /test_mynotebook - Lifecycle State: TERMINATED, Result: FAILED\n'
    expected_view += 'Run Page URL: {}\n'.format(notebook_results.notebook_run_page_url)
    expected_view += '============================================================\n'
    expected_view += 'FAILING TESTS\n'
    expected_view += '------------------------------------------------------------\n'
    expected_view += test_case_result_view.get_view()
    expected_view += '\n\n'
    expected_view += '============================================================\n'

    run_results_view = RunCommandResultsView()
    run_results_view.add_exec_result(notebook_results)

    view = run_results_view.get_view()

    assert expected_view == view


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
