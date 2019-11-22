"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import os
import json
from common.api import Nutter, TestNotebook, NutterStatusEvents
import common.api as nutter_api
from common.testresult import TestResults, TestResult
from common.api import TestNamePatternMatcher
from common.resultreports import JunitXMLReportWriter
from common.resultreports import TagsReportWriter
from common.apiclient import WorkspacePath, DatabricksAPIClient
from common.statuseventhandler import StatusEventsHandler, EventHandler, StatusEvent

def test__workspacepath__empty_object_response__instance_is_created():
    objects = {}
    workspace_path = WorkspacePath.from_api_response(objects)

def test__get_report_writer__junitxmlreportwriter__valid_instance():
    writer = nutter_api.get_report_writer('JunitXMLReportWriter')

    assert isinstance(writer, JunitXMLReportWriter)


def test__get_report_writer__tagsreportwriter__valid_instance():
    writer = nutter_api.get_report_writer('TagsReportWriter')

    assert isinstance(writer, TagsReportWriter)


def test__list_tests__onetest__okay(mocker):

    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/mynotebook'), ('NOTEBOOK', '/test_mynotebook')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/")

    assert len(tests) == 1
    assert tests[0] == TestNotebook('test_mynotebook', '/test_mynotebook')


def test__list_tests__onetest_in_folder__okay(mocker):

    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/folder/mynotebook'), ('NOTEBOOK', '/folder/test_mynotebook')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/folder")

    assert len(tests) == 1
    assert tests[0] == TestNotebook(
        'test_mynotebook', '/folder/test_mynotebook')


@pytest.mark.skip('No longer needed')
def test__list_tests__response_without_root_object__okay(mocker):

    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    objects = """{"objects":[
    {"object_type":"NOTEBOOK","path":"/mynotebook","language":"PYTHON"},
    {"object_type":"NOTEBOOK","path":"/test_mynotebook","language":"PYTHON"}]}"""

    nutter.dbclient.list_notebooks.return_value = WorkspacePath(json.loads(objects)[
        'objects'])

    tests = nutter.list_tests("/")

    assert len(tests) == 1
    assert tests[0] == TestNotebook('test_mynotebook', '/test_mynotebook')


def test__list_tests__onetest_uppercase_name__okay(mocker):

    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/mynotebook'), ('NOTEBOOK', '/TEST_mynote')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/")

    assert len(tests) == 1
    assert tests == [TestNotebook('TEST_mynote', '/TEST_mynote')]


def test__list_tests__nutterstatusevents_testlisting_sequence_is_fired(mocker):
    event_handler = TestEventHandler()
    nutter = _get_nutter(mocker, event_handler)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/mynotebook'), ('NOTEBOOK', '/TEST_mynote')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/")
    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListing

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListingResults
    assert status_event.data == 1

def test__list_tests_recursively__1test1dir1test__2_tests(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/test_1'), ('DIRECTORY', '/p')])
    workspace_path_2 = _get_workspacepathobject([('NOTEBOOK', '/p/test_1')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2]

    tests = nutter.list_tests("/", True)

    expected = [TestNotebook('test_1', '/test_1'),
                TestNotebook('test_1', '/p/test_1')]
    assert expected == tests
    assert nutter.dbclient.list_objects.call_count == 2


def test__list_tests_recursively__1test1dir2test__3_tests(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/test_1'), ('DIRECTORY', '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [('NOTEBOOK', '/p/test_1'), ('NOTEBOOK', '/p/test_2')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2]

    tests = nutter.list_tests("/", True)
    expected = [TestNotebook('test_1', '/test_1'), TestNotebook('test_1',
                                                                '/p/test_1'), TestNotebook('test_2', '/p/test_2')]
    assert expected == tests
    assert nutter.dbclient.list_objects.call_count == 2


def test__list_tests_recursively__1test1dir1dir__1_test(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/test_1'), ('DIRECTORY', '/p')])
    workspace_path_2 = _get_workspacepathobject([('DIRECTORY', '/p/c')])
    workspace_path_3 = _get_workspacepathobject([])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2, workspace_path_3]

    tests = nutter.list_tests("/", True)

    expected = [TestNotebook('test_1', '/test_1')]
    assert expected == tests
    assert nutter.dbclient.list_objects.call_count == 3


def test__list_tests__notest__empty_list(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [
                                ('NOTEBOOK', '/my'), ('NOTEBOOK', '/my2')])

    results = nutter.list_tests("/")

    assert len(results) == 0



def test__run_tests__onematch_two_tests___nutterstatusevents_testlisting_scheduling_execution_sequence_is_fired(mocker):
    event_handler = TestEventHandler()
    nutter = _get_nutter(mocker, event_handler)
    test_results = TestResults()
    test_results.append(TestResult('case',True, 10,[]))
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', test_results.serialize())
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/test_my'), ('NOTEBOOK', '/test_abc')])

    results = nutter.run_tests("/my*", "cluster")

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecutionRequest
    assert status_event.data == '/my*'

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListing

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListingResults
    assert status_event.data == 2

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListingFiltered
    assert status_event.data == 1

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestScheduling
    assert status_event.data == '/test_my'

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecuted
    assert status_event.data.success

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecutionResult
    assert status_event.data #True if success


def test__run_tests__onematch__okay(mocker):
    nutter = _get_nutter(mocker)
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/test_my'), ('NOTEBOOK', '/my')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 1
    result = results[0]
    assert result.task_result_state == 'TERMINATED'

def test__run_tests_recursively__1test1dir2test__3_tests(mocker):
    nutter = _get_nutter(mocker)
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)
    nutter.dbclient = dbapi_client

    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('NOTEBOOK', '/test_1'), ('DIRECTORY', '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [('NOTEBOOK', '/p/test_1'), ('NOTEBOOK', '/p/test_2')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2]

    tests = nutter.run_tests('/','cluster', 120, 1, True)
    assert len(tests) == 3

def test__run_tests_recursively__1dir1dir2test__2_tests(mocker):
    nutter = _get_nutter(mocker)
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)
    nutter.dbclient = dbapi_client

    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [('DIRECTORY', '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [('DIRECTORY', '/c')])
    workspace_path_3 = _get_workspacepathobject(
        [('NOTEBOOK', '/p/c/test_1'), ('NOTEBOOK', '/p/c/test_2')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2, workspace_path_3]

    tests = nutter.run_tests('/','cluster', 120, 1, True)
    assert len(tests) == 2

def test__run_tests__onematch_suffix_is_uppercase__okay(mocker):
    nutter = _get_nutter(mocker)
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/TEST_my'), ('NOTEBOOK', '/my')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 1
    assert results[0].task_result_state == 'TERMINATED'


def test__run_tests__nomatch_case_sensitive__okay(mocker):
    nutter = _get_nutter(mocker)
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/test_MY'), ('NOTEBOOK', '/my')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 0


def test__run_tests__twomatches_with_pattern__okay(mocker):
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)

    nutter = _get_nutter(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/test_my'), ('NOTEBOOK', '/test_my2')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 2
    assert results[0].task_result_state == 'TERMINATED'
    assert results[1].task_result_state == 'TERMINATED'


def test__run_tests__with_invalid_pattern__valueerror(mocker):
    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)
    nutter = _get_nutter(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/test_my'), ('NOTEBOOK', '/test_my2')])

    with pytest.raises(ValueError):
        results = nutter.run_tests("/my/(", "cluster")


def test__run_tests__nomatches__okay(mocker):

    submit_response = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response)
    nutter = _get_nutter(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        'NOTEBOOK', '/test_my'), ('NOTEBOOK', '/test_my2')])

    results = nutter.run_tests("/abc*", "cluster")

    assert len(results) == 0


def test__to_testresults__none_output__none(mocker):
    output = None
    result = nutter_api.to_testresults(output)

    assert result is None


def test__to_testresults__non_pickle_output__none(mocker):
    output = 'NOT A PICKLE'
    result = nutter_api.to_testresults(output)

    assert result is None


def test__to_testresults__pickle_output__testresult(mocker):
    output = TestResults().serialize()
    result = nutter_api.to_testresults(output)

    assert isinstance(result, TestResults)


patterns = [
    (''),
    ('*'),
    (None),
    ('abc'),
    ('abc*'),
]
@pytest.mark.parametrize('pattern', patterns)
def test__testnamepatternmatcher_ctor_valid_pattern__instance(pattern):
    pattern_matcher = TestNamePatternMatcher(pattern)

    assert isinstance(pattern_matcher, TestNamePatternMatcher)


all_patterns = [
    (''),
    ('*'),
    (None),
]
@pytest.mark.parametrize('pattern', all_patterns)
def test__testnamepatternmatcher_ctor_valid_all_pattern__pattern_is_none(pattern):
    pattern_matcher = TestNamePatternMatcher(pattern)

    assert isinstance(pattern_matcher, TestNamePatternMatcher)
    assert pattern_matcher._pattern is None


reg_patterns = [
    ('t?as'),
    ('tt*'),
    ('e^6'),
]
@pytest.mark.parametrize('pattern', reg_patterns)
def test__testnamepatternmatcher_ctor_valid_regex_pattern__pattern_is_pattern(pattern):
    pattern_matcher = TestNamePatternMatcher(pattern)

    assert isinstance(pattern_matcher, TestNamePatternMatcher)
    assert pattern_matcher._pattern == pattern


filter_patterns = [
    ('', [], 0),
    ('a', [TestNotebook("test_a", "/test_a")], 1),
    ('*', [TestNotebook("test_a", "/test_a"), TestNotebook("test_b", "/test_b")], 2),
    ('b*',[TestNotebook("test_a", "/test_a"), TestNotebook("test_b", "/test_b")], 1),
    ('b*',[TestNotebook("test_ba", "/test_ba"), TestNotebook("test_b", "/test_b")], 2),
    ('c*',[TestNotebook("test_a", "/test_a"), TestNotebook("test_b", "/test_b")], 0),
]
@pytest.mark.parametrize('pattern, list_results, expected_count', filter_patterns)
def test__filter_by_pattern__valid_scenarios__result_len_is_expected_count(pattern, list_results, expected_count):

    pattern_matcher = TestNamePatternMatcher(pattern)
    filtered = pattern_matcher.filter_by_pattern(list_results)

    assert len(filtered) == expected_count


invalid_patterns = [
    ('('),
    ('--)'),
]
@pytest.mark.parametrize('pattern', invalid_patterns)
def test__testnamepatternmatcher_ctor__invali_pattern__valueerror(pattern):

    with pytest.raises(ValueError):
        pattern_matcher = TestNamePatternMatcher(pattern)


def _get_submit_run_response(result_state, life_cycle_state, result):
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
    data_dict['metadata']['state']['result_state'] = result_state
    data_dict['metadata']['state']['life_cycle_state'] = life_cycle_state

    return json.dumps(data_dict)


def _get_client_for_execute_notebook(mocker, output_data):
    run_id = {}
    run_id['run_id'] = 1

    db = _get_client(mocker)
    mocker.patch.object(db.inner_dbclient.jobs, 'submit_run')
    db.inner_dbclient.jobs.submit_run.return_value = run_id
    mocker.patch.object(db.inner_dbclient.jobs, 'get_run_output')
    db.inner_dbclient.jobs.get_run_output.return_value = json.loads(
        output_data)

    return db


def _get_client(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    return DatabricksAPIClient()


def _get_nutter(mocker, event_handler = None):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    return Nutter(event_handler)


def _mock_dbclient_list_objects(mocker, dbclient, objects):
    mocker.patch.object(dbclient, 'list_objects')

    workspace_objects = _get_workspacepathobject(objects)
    dbclient.list_objects.return_value = workspace_objects


def _get_workspacepathobject(objects):
    objects_list = []
    for object in objects:
        item = {}
        item['object_type'] = object[0]
        item['path'] = object[1]
        item['language'] = 'PYTHON'
        objects_list.append(item)

    root_obj = {'objects': objects_list}

    return WorkspacePath.from_api_response(root_obj)


class TestEventHandler(EventHandler):
    def __init__(self):
        self._queue = None
        super().__init__()

    def handle(self, queue):
        self._queue = queue

    def get_item(self):
        item = self._queue.get()
        self._queue.task_done()
        return item

