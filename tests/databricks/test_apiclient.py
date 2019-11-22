"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from common import apiclient as client
from common.apiclient import DatabricksAPIClient
import os
import json


def test__databricks_client__token_host_notset__clientfails(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': ''})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': ''})

    with pytest.raises(client.InvalidConfigurationException):
        dbclient = client.databricks_client()


def test__databricks_client__token_host_set__clientreturns(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    dbclient = client.databricks_client()

    assert isinstance(dbclient, DatabricksAPIClient)


def test__list_notebooks__onenotebook__okay(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.inner_dbclient.workspace, 'list')

    objects = """{"objects":[
    {"object_type":"NOTEBOOK","path":"/nutfixjob","language":"PYTHON"},
    {"object_type":"DIRECTORY","path":"/ETL-Part-3-1.0.3"}]}"""

    db.inner_dbclient.workspace.list.return_value = json.loads(objects)

    notebooks = db.list_notebooks('/')

    assert len(notebooks) == 1


def test__list_notebooks__zeronotebook__okay(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.inner_dbclient.workspace, 'list')

    objects = """{"objects":[
    {"object_type":"DIRECTORY","path":"/ETL-Part-3-1.0.3"}]}"""

    db.inner_dbclient.workspace.list.return_value = json.loads(objects)

    notebooks = db.list_notebooks('/')

    assert len(notebooks) == 0


def test__execute_notebook__emptypath__valueerrror(mocker):
    db = __get_client(mocker)

    with pytest.raises(ValueError):
        db.execute_notebook('', 'cluster')


def test__execute_notebook__nonepath__valueerror(mocker):
    db = __get_client(mocker)

    with pytest.raises(ValueError):
        db.execute_notebook(None, 'cluster')


def test__execute_notebook__emptycluster__valueerror(mocker):
    db = __get_client(mocker)

    with pytest.raises(ValueError):
        db.execute_notebook('/', '')


def test__execute_notebook__non_dict_params__valueerror(mocker):
    db = __get_client(mocker)

    with pytest.raises(ValueError):
        db.execute_notebook('/', 'cluster', notebook_params='')


def test__execute_notebook__nonecluster__valueerror(mocker):
    db = __get_client(mocker)

    with pytest.raises(ValueError):
        db.execute_notebook('/', None)


def test__execute_notebook__success__executeresult_has_run_url(mocker):
    run_page_url = "http://runpage"
    output_data = __get_submit_run_response(
        'SUCCESS', 'TERMINATED', '', run_page_url)
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.notebook_run_page_url == run_page_url

def test__execute_notebook__failure__executeresult_has_run_url(mocker):
    run_page_url = "http://runpage"
    output_data = __get_submit_run_response(
        'FAILURE', 'TERMINATED', '', run_page_url)
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.notebook_run_page_url == run_page_url


def test__execute_notebook__terminatestate__success(mocker):
    output_data = __get_submit_run_response('SUCCESS', 'TERMINATED', '')
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.task_result_state == 'TERMINATED'


def test__execute_notebook__skippedstate__resultstate_is_SKIPPED(mocker):
    output_data = __get_submit_run_response('', 'SKIPPED', '')
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.task_result_state == 'SKIPPED'


def test__execute_notebook__internal_error_state__resultstate_is_INTERNAL_ERROR(mocker):
    output_data = __get_submit_run_response('', 'INTERNAL_ERROR', '')
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.task_result_state == 'INTERNAL_ERROR'


def test__execute_notebook__timeout_1_sec_lcs_isrunning__timeoutexception(mocker):
    output_data = __get_submit_run_response('', 'RUNNING', '')
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    with pytest.raises(client.TimeOutException):
        db.min_timeout = 1
        result = db.execute_notebook('/mynotebook', 'clusterid', timeout=1)


def test__execute_notebook__timeout_greater_than_min__valueerror(mocker):
    output_data = __get_submit_run_response('', 'RUNNING', '')
    run_id = {}
    run_id['run_id'] = 1
    db = __get_client_for_execute_notebook(mocker, output_data, run_id)

    with pytest.raises(ValueError):
        db.min_timeout = 10
        result = db.execute_notebook('/mynotebook', 'clusterid', timeout=1)


default_run_page_url = 'https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1'


def __get_submit_run_response(task_result_state, life_cycle_state, result, run_page_url=default_run_page_url):
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
                "task": {"notebook_task": {"notebook_path": "/mynotebook"}},
                "run_id": 7, "start_time": 1569887259173,
                "job_id": 4,
                "state": {"result_state": "SUCCESS", "state_message": "",
                "life_cycle_state": "TERMINATED"}, "setup_duration": 2000,
                "run_page_url": "https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1",
                "cluster_spec": {"existing_cluster_id": "0925-141122-narcs242"}, "run_name": "myrun"}}
                """
    data_dict = json.loads(data_json)
    data_dict['notebook_output']['result'] = result
    data_dict['metadata']['state']['result_state'] = task_result_state
    data_dict['metadata']['state']['life_cycle_state'] = life_cycle_state
    data_dict['metadata']['run_page_url'] = run_page_url

    return json.dumps(data_dict)


def __get_client_for_execute_notebook(mocker, output_data, run_id):
    db = __get_client(mocker)
    mocker.patch.object(db.inner_dbclient.jobs, 'submit_run')
    db.inner_dbclient.jobs.submit_run.return_value = run_id
    mocker.patch.object(db.inner_dbclient.jobs, 'get_run_output')
    db.inner_dbclient.jobs.get_run_output.return_value = json.loads(
        output_data)

    return db


def __get_client(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    return DatabricksAPIClient()
