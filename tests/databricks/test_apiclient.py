"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from common import apiclient as client
from common.apiclient import DatabricksAPIClient
import os

from databricks.sdk.service.jobs import Run, RunTask, NotebookTask, RunState, \
    RunLifeCycleState, RunResultState, RunOutput, NotebookOutput
from databricks.sdk.service.workspace import ObjectType, ObjectInfo, Language
from databricks.sdk.service.compute import ClusterDetails


def test__databricks_client__token_host_notset__clientfails(mocker):
    from databricks.sdk import WorkspaceClient
    
    # Mock WorkspaceClient to raise ValueError when credentials are missing
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': '', 'DATABRICKS_TOKEN': ''})
    mocker.patch.object(WorkspaceClient, '__init__', side_effect=ValueError("cannot configure default credentials"))

    with pytest.raises(ValueError):
        dbclient = client.databricks_client()


def test__databricks_client__token_host_set__clientreturns(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    dbclient = client.databricks_client()

    assert isinstance(dbclient, DatabricksAPIClient)


def test__list_notebooks__onenotebook__okay(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.workspace, 'list')

    objects = [
        ObjectInfo(object_type=ObjectType.NOTEBOOK, path="/nutfixjob", language=Language.PYTHON),
        ObjectInfo(object_type=ObjectType.DIRECTORY, path="/ETL-Part-3-1.0.3")
    ]

    db.dbclient.workspace.list.return_value = iter(objects)

    notebooks = db.list_notebooks('/')

    assert len(notebooks) == 1


def test__list_notebooks__zeronotebook__okay(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.workspace, 'list')

    objects = [
        ObjectInfo(object_type=ObjectType.DIRECTORY, path="/ETL-Part-3-1.0.3")
    ]

    db.dbclient.workspace.list.return_value = iter(objects)

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
    run_info, run_output = __get_submit_run_response(
        'SUCCESS', 'TERMINATED', '', run_page_url)
    db = __get_client_for_execute_notebook(mocker, run_info, run_output)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.notebook_run_page_url == run_page_url

def test__execute_notebook__failure__executeresult_has_run_url(mocker):
    run_page_url = "http://runpage"
    run_info, run_output = __get_submit_run_response(
        'FAILED', 'TERMINATED', '', run_page_url)
    db = __get_client_for_execute_notebook(mocker, run_info, run_output)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.notebook_run_page_url == run_page_url


def test__execute_notebook__terminatestate__success(mocker):
    run_info, run_output = __get_submit_run_response('SUCCESS', 'TERMINATED', '')
    db = __get_client_for_execute_notebook(mocker, run_info, run_output)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.task_result_state == 'TERMINATED'


def test__execute_notebook__skippedstate__resultstate_is_SKIPPED(mocker):
    run_info, run_output = __get_submit_run_response('', 'SKIPPED', '')
    db = __get_client_for_execute_notebook(mocker, run_info, run_output)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.task_result_state == 'SKIPPED'


def test__execute_notebook__internal_error_state__resultstate_is_INTERNAL_ERROR(mocker):
    run_info, run_output = __get_submit_run_response('', 'INTERNAL_ERROR', '')
    db = __get_client_for_execute_notebook(mocker, run_info, run_output)

    result = db.execute_notebook('/mynotebook', 'clusterid')

    assert result.task_result_state == 'INTERNAL_ERROR'


def test__execute_notebook__timeout_1_sec_lcs_isrunning__timeoutexception(mocker):
    run_info, run_output = __get_submit_run_response('', 'RUNNING', '')
    db = __get_client(mocker)
    
    # Make submit_and_wait raise TimeOutException when called
    mocker.patch.object(db.dbclient.jobs, 'submit_and_wait')
    db.dbclient.jobs.submit_and_wait.side_effect = client.TimeOutException("Timeout waiting for job")

    with pytest.raises(client.TimeOutException):
        db.min_timeout = 1
        result = db.execute_notebook('/mynotebook', 'clusterid', timeout=1)


def test__execute_notebook__timeout_greater_than_min__valueerror(mocker):
    run_info, run_output = __get_submit_run_response('', 'RUNNING', '')
    db = __get_client_for_execute_notebook(mocker, run_info, run_output)

    with pytest.raises(ValueError):
        db.min_timeout = 10
        result = db.execute_notebook('/mynotebook', 'clusterid', timeout=1)


default_run_page_url = 'https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1'


def __get_submit_run_response(task_result_state, life_cycle_state, result, run_page_url=default_run_page_url):
    # Create proper SDK objects instead of JSON
    result_state = getattr(RunResultState, task_result_state) if task_result_state else None
    lifecycle_state = getattr(RunLifeCycleState, life_cycle_state)
    
    run_info = Run(
        tasks=[
            RunTask(
                task_key="test_task",
                notebook_task=NotebookTask(notebook_path="/mynotebook"),
                run_id=2,
                state=RunState(
                    life_cycle_state=lifecycle_state,
                    result_state=result_state,
                    state_message=""
                )
            )
        ],
        run_id=1,
        run_page_url=run_page_url,
        state=RunState(
            life_cycle_state=lifecycle_state,
            result_state=result_state,
            state_message=""
        ),
    )
    
    notebook_output = RunOutput(
        notebook_output=NotebookOutput(result=result, truncated=False)
    )
    
    return run_info, notebook_output


def __get_client_for_execute_notebook(mocker, run_info, run_output):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.jobs, 'submit_and_wait')
    db.dbclient.jobs.submit_and_wait.return_value = run_info
    mocker.patch.object(db.dbclient.jobs, 'get_run_output')
    db.dbclient.jobs.get_run_output.return_value = run_output

    return db


def __get_client(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    return DatabricksAPIClient()


def test__get_cluster_id_by_name__cluster_found__returns_id(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.clusters, 'list')
    
    # Mock clusters list response
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='test-cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='other-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    
    cluster_id = db.get_cluster_id_by_name('test-cluster')
    
    assert cluster_id == '1234-567890-abcd'


def test__get_cluster_id_by_name__empty_name__raises_error(mocker):
    db = __get_client(mocker)
    
    with pytest.raises(ValueError, match="empty cluster name"):
        db.get_cluster_id_by_name('')


def test__get_cluster_id_by_name__cluster_not_found__raises_error(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.clusters, 'list')
    
    # Mock clusters list response
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='test-cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='other-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    
    with pytest.raises(ValueError, match="No cluster found with name 'nonexistent-cluster'"):
        db.get_cluster_id_by_name('nonexistent-cluster')


def test__get_cluster_id_by_name__multiple_clusters_with_same_name__raises_error(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.clusters, 'list')
    
    # Mock clusters list response with duplicate names
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='duplicate-cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='duplicate-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    
    with pytest.raises(ValueError, match="Multiple clusters found with name 'duplicate-cluster'"):
        db.get_cluster_id_by_name('duplicate-cluster')


def test__get_cluster_id_by_name__case_insensitive__returns_id(mocker):
    db = __get_client(mocker)
    
    # Test lowercase
    mocker.patch.object(db.dbclient.clusters, 'list')
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='Test-Cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='other-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    cluster_id = db.get_cluster_id_by_name('test-cluster')
    assert cluster_id == '1234-567890-abcd'
    
    # Test uppercase
    mocker.patch.object(db.dbclient.clusters, 'list')
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='Test-Cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='other-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    cluster_id = db.get_cluster_id_by_name('TEST-CLUSTER')
    assert cluster_id == '1234-567890-abcd'
    
    # Test mixed case
    mocker.patch.object(db.dbclient.clusters, 'list')
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='Test-Cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='other-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    cluster_id = db.get_cluster_id_by_name('TeSt-ClUsTeR')
    assert cluster_id == '1234-567890-abcd'


def test__get_cluster_id_by_name__multiple_clusters_case_insensitive__raises_error(mocker):
    db = __get_client(mocker)
    mocker.patch.object(db.dbclient.clusters, 'list')
    
    # Mock clusters list response with duplicate names in different cases
    clusters = [
        ClusterDetails(cluster_id='1234-567890-abcd', cluster_name='Test-Cluster'),
        ClusterDetails(cluster_id='9876-543210-wxyz', cluster_name='test-cluster')
    ]
    db.dbclient.clusters.list.return_value = iter(clusters)
    
    with pytest.raises(ValueError, match="Multiple clusters found with name"):
        db.get_cluster_id_by_name('TEST-CLUSTER')


def test__execute_notebook__with_serverless__success(mocker):
    db = __get_client(mocker)
    run_info, run_output = __get_submit_run_response('SUCCESS', 'TERMINATED', 'result')
    mocker.patch.object(db.dbclient.jobs, 'submit_and_wait')
    db.dbclient.jobs.submit_and_wait.return_value = run_info
    mocker.patch.object(db.dbclient.jobs, 'get_run_output')
    db.dbclient.jobs.get_run_output.return_value = run_output
    
    result = db.execute_notebook('/mynotebook', serverless=1, timeout=120)
    
    # Verify submit_and_wait was called with environments
    assert db.dbclient.jobs.submit_and_wait.call_count == 1
    call_kwargs = db.dbclient.jobs.submit_and_wait.call_args[1]
    assert 'environments' in call_kwargs
    assert len(call_kwargs['environments']) == 1
    assert call_kwargs['environments'][0].environment_key == 'serverless'
    assert call_kwargs['environments'][0].spec.environment_version == '1'
    
    # Verify task has environment_key instead of cluster_id
    tasks = db.dbclient.jobs.submit_and_wait.call_args[1]['tasks']
    assert tasks[0].environment_key == 'serverless'
    assert tasks[0].existing_cluster_id is None


def test__execute_notebook__no_compute__raises_error(mocker):
    db = __get_client(mocker)
    
    with pytest.raises(ValueError, match="either cluster_id or serverless must be specified"):
        db.execute_notebook('/mynotebook', timeout=120)


def test__execute_notebook__both_cluster_and_serverless__raises_error(mocker):
    db = __get_client(mocker)
    
    with pytest.raises(ValueError, match="cannot specify both cluster_id and serverless"):
        db.execute_notebook('/mynotebook', cluster_id='cluster-123', serverless=1, timeout=120)


def test__execute_notebook__serverless_not_integer__raises_error(mocker):
    db = __get_client(mocker)
    
    # Test with string
    with pytest.raises(ValueError, match="serverless must be an integer"):
        db.execute_notebook('/mynotebook', serverless='1.0', timeout=120)
    
    # Test with float
    with pytest.raises(ValueError, match="serverless must be an integer"):
        db.execute_notebook('/mynotebook', serverless=1.0, timeout=120)
