"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import os
from unittest.mock import Mock
from databricks.sdk.service.jobs import Run, RunTask, NotebookTask, RunState, \
    RunLifeCycleState, RunResultState, RunOutput, NotebookOutput

import cli.nuttercli as nuttercli
from cli.nuttercli import NutterCLI
from common.apiclientresults import ExecuteNotebookResult
from common.utils import BUILD_NUMBER_ENV_VAR
import mock
from common.testresult import TestResults, TestResult
from cli.reportsman import ReportWriterManager, ReportWritersTypes, ReportWriters


def test__get_cli_version__without_build__env_var__returns_value():
    version = nuttercli.get_nutter_version()
    assert version is not None


def test__get_cli_header_value():
    version = nuttercli.get_nutter_version()
    header = 'Nutter Version {}\n'.format(version)
    header += '+' * 50
    header += '\n'

    assert nuttercli.get_cli_header() == header



def test__get_cli_version__with_build__env_var__returns_value(mocker):
    version = nuttercli.get_nutter_version()
    build_number = '1.2.3'
    mocker.patch.dict(
        os.environ, {BUILD_NUMBER_ENV_VAR: build_number})
    version_with_build_number = nuttercli.get_nutter_version()
    assert version_with_build_number == '{}.{}'.format(version, build_number)

def test__get_version_label__valid_string(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    version = nuttercli.get_nutter_version()
    expected = 'Nutter Version {}'.format(version)
    cli = NutterCLI()
    version_from_cli =  cli._get_version_label()

    assert expected == version_from_cli


def test__nutter_cli_ctor__handles__version_and_exits_0(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})


    with pytest.raises(SystemExit) as mock_ex:
        cli = NutterCLI(version=True)

    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 0

def test__run__pattern__display_results(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)

    mocker.patch.object(cli, '_display_test_results')
    cli.run('my*', 'cluster')
    assert cli._display_test_results.call_count == 1


def test__nutter_cli_ctor__handles__configurationexception_and_exits_1(mocker):
    from databricks.sdk import WorkspaceClient
    
    # Mock WorkspaceClient to raise ValueError when credentials are missing
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': '', 'DATABRICKS_TOKEN': ''})
    mocker.patch.object(WorkspaceClient, '__init__', side_effect=ValueError("cannot configure default credentials"))

    with pytest.raises(SystemExit) as mock_ex:
        cli = NutterCLI()

    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 1


def test__run__one_test_fullpath__display_results(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)

    mocker.patch.object(cli, '_display_test_results')
    cli.run('test_mynotebook2', 'cluster')
    assert cli._display_test_results.call_count == 1

def test__run_one_test_junit_writter__writer_writes(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    mocker.patch.object(cli, '_get_report_writer_manager')
    mock_report_manager = ReportWriterManager(ReportWriters.JUNIT)
    mocker.patch.object(mock_report_manager, 'write')
    mocker.patch.object(mock_report_manager, 'add_result')

    cli._get_report_writer_manager.return_value = mock_report_manager

    cli.run('test_mynotebook2', 'cluster')

    assert mock_report_manager.add_result.call_count == 1
    assert mock_report_manager.write.call_count == 1
    assert not mock_report_manager._providers[ReportWritersTypes.JUNIT].has_data(
    )


def test__list__none__display_result(mocker):
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', 'IHAVERETURNED')

    mocker.patch.object(cli, '_display_list_results')
    cli.list('/')
    assert cli._display_list_results.call_count == 1


def _get_cli_for_tests(mocker, result_state, life_cycle_state, notebook_result):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})
    cli = NutterCLI()
    mocker.patch.object(cli._nutter, 'run_test')
    cli._nutter.run_test.return_value = _get_run_test_response(
        result_state, life_cycle_state, notebook_result)
    mocker.patch.object(cli._nutter, 'run_tests')
    cli._nutter.run_tests.return_value = _get_run_tests_response(
        result_state, life_cycle_state, notebook_result)
    mocker.patch.object(cli._nutter, 'list_tests')
    cli._nutter.list_tests.return_value = _get_list_tests_response()

    return cli


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


def _get_list_tests_response():
    result = {}
    result['test_mynotebook'] = '/test_mynotebook'
    result['test_mynotebook2'] = '/test_mynotebook2'
    return result


def _get_run_tests_response(result_state, life_cycle_state, notebook_result):
    # Create proper SDK objects for two test results
    result_state_enum = getattr(RunResultState, result_state) if result_state else None
    lifecycle_state_enum = getattr(RunLifeCycleState, life_cycle_state)
    
    # First result
    run_info1 = Run(
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
    
    # Second result with different notebook path
    run_info2 = Run(
        tasks=[
            RunTask(
                task_key="test_task",
                notebook_task=NotebookTask(notebook_path="/test_mynotebook2"),
                run_id=3,
                state=RunState(
                    life_cycle_state=lifecycle_state_enum,
                    result_state=result_state_enum,
                    state_message=""
                )
            )
        ],
        run_id=2,
        run_page_url="https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1",
        state=RunState(
            life_cycle_state=lifecycle_state_enum,
            result_state=result_state_enum,
            state_message=""
        ),
    )
    
    # Create mock WorkspaceClients
    mock_client1 = Mock()
    mock_client1.jobs.get_run_output.return_value = RunOutput(
        notebook_output=NotebookOutput(result=notebook_result, truncated=False)
    )
    
    mock_client2 = Mock()
    mock_client2.jobs.get_run_output.return_value = RunOutput(
        notebook_output=NotebookOutput(result=notebook_result, truncated=False)
    )
    
    results = []
    results.append(ExecuteNotebookResult.from_job_output(run_info1, mock_client1))
    results.append(ExecuteNotebookResult.from_job_output(run_info2, mock_client2))
    return results


def test__run__with_cluster_name__resolves_to_cluster_id(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    # Mock the get_cluster_id_by_name method
    mocker.patch.object(cli._nutter.dbclient, 'get_cluster_id_by_name')
    cli._nutter.dbclient.get_cluster_id_by_name.return_value = 'resolved-cluster-id'
    
    mocker.patch.object(cli, '_display_test_results')
    cli.run('test_mynotebook2', cluster_name='my-cluster')
    
    # Verify that get_cluster_id_by_name was called with the correct name
    cli._nutter.dbclient.get_cluster_id_by_name.assert_called_once_with('my-cluster')
    assert cli._display_test_results.call_count == 1


def test__run__with_both_cluster_id_and_name__exits_with_error(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    # Should exit with error when both cluster_id and cluster_name are provided
    with pytest.raises(SystemExit) as mock_ex:
        cli.run('test_mynotebook2', cluster_id='cluster-id', cluster_name='cluster-name')
    
    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 1


def test__run__with_neither_cluster_id_nor_name__exits_with_error(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    # Should exit with error when neither cluster_id nor cluster_name is provided
    with pytest.raises(SystemExit) as mock_ex:
        cli.run('test_mynotebook2')
    
    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 1


def test__run__with_cluster_name_resolution_fails__exits_with_error(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    # Mock the get_cluster_id_by_name method to raise ValueError
    mocker.patch.object(cli._nutter.dbclient, 'get_cluster_id_by_name')
    cli._nutter.dbclient.get_cluster_id_by_name.side_effect = ValueError("Cluster not found")
    
    # Should exit with error when cluster name resolution fails
    with pytest.raises(SystemExit) as mock_ex:
        cli.run('test_mynotebook2', cluster_name='nonexistent-cluster')
    
    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 1


def test__run__with_serverless__executes_successfully(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    mocker.patch.object(cli, '_display_test_results')
    cli.run('test_mynotebook2', serverless=1)
    
    # Verify that run_test was called with serverless parameter
    assert cli._nutter.run_test.call_count == 1
    call_kwargs = cli._nutter.run_test.call_args[1]
    assert call_kwargs['serverless'] == 1
    assert call_kwargs['cluster_id'] is None
    assert cli._display_test_results.call_count == 1


def test__run__with_serverless_and_cluster_id__exits_with_error(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    # Should exit with error when both serverless and cluster_id are provided
    with pytest.raises(SystemExit) as mock_ex:
        cli.run('test_mynotebook2', cluster_id='cluster-123', serverless=1)
    
    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 1


def test__run__with_no_compute_option__exits_with_error(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    # Should exit with error when no compute option is provided
    with pytest.raises(SystemExit) as mock_ex:
        cli.run('test_mynotebook2')
    
    assert mock_ex.type == SystemExit
    assert mock_ex.value.code == 1


def test__run__pattern_with_serverless__executes_successfully(mocker):
    test_results = TestResults().serialize()
    cli = _get_cli_for_tests(
        mocker, 'SUCCESS', 'TERMINATED', test_results)
    
    mocker.patch.object(cli, '_display_test_results')
    cli.run('my*', serverless=1)
    
    # Verify that run_tests was called with serverless parameter
    assert cli._nutter.run_tests.call_count == 1
    call_kwargs = cli._nutter.run_tests.call_args[1]
    assert call_kwargs['serverless'] == 1
    assert call_kwargs['cluster_id'] is None
    assert cli._display_test_results.call_count == 1
