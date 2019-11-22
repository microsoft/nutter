"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import os
import json
import cli.nuttercli as nuttercli
from cli.nuttercli import NutterCLI
from common.apiclientresults import ExecuteNotebookResult
import mock
from common.testresult import TestResults, TestResult
from cli.reportsman import ReportWriterManager, ReportWritersTypes, ReportWriters


def test__get_cli_version__without_build__env_var__returns_value():
    version = nuttercli.get_cli_version()
    assert version is not None


def test__get_cli_header_value():
    version = nuttercli.get_cli_version()
    header = 'Nutter Version {}\n'.format(version)
    header += '+' * 50
    header += '\n'

    assert nuttercli.get_cli_header() == header



def test__get_cli_version__with_build__env_var__returns_value(mocker):
    version = nuttercli.get_cli_version()
    build_number = '1.2.3'
    mocker.patch.dict(
        os.environ, {nuttercli.BUILD_NUMBER_ENV_VAR: build_number})
    version_with_build_number = nuttercli.get_cli_version()
    assert version_with_build_number == '{}.{}'.format(version, build_number)

def test__get_version_label__valid_string(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    version = nuttercli.get_cli_version()
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
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': ''})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': ''})

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


def _get_list_tests_response():
    result = {}
    result['test_mynotebook'] = '/test_mynotebook'
    result['test_mynotebook2'] = '/test_mynotebook2'
    return result


def _get_run_tests_response(result_state, life_cycle_state, notebook_result):
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

    data_dict2 = json.loads(data_json)
    data_dict2['notebook_output']['result'] = notebook_result
    data_dict2['metadata']['state']['result_state'] = result_state
    data_dict2['metadata']['task']['notebook_task']['notebook_path'] = '/test_mynotebook2'
    data_dict2['metadata']['state']['life_cycle_state'] = life_cycle_state

    results = []
    results.append(ExecuteNotebookResult.from_job_output(data_dict))
    results.append(ExecuteNotebookResult.from_job_output(data_dict2))
    return results
