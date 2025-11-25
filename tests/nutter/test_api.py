"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import os
import json

from databricks.sdk.service.jobs import Run, Task, NotebookTask, RunTask, RunState, \
    RunLifeCycleState, RunResultState, RunOutput, NotebookOutput

from common.api import Nutter, TestNotebook, NutterStatusEvents
import common.api as nutter_api
from common.testresult import TestResults, TestResult
from common.api import TestNamePatternMatcher
from common.resultreports import JunitXMLReportWriter
from common.resultreports import TagsReportWriter
from common.apiclient import WorkspacePath, DatabricksAPIClient
from common.statuseventhandler import StatusEventsHandler, EventHandler, StatusEvent

from databricks.sdk.service.workspace import ObjectType, ObjectInfo, Language


def test__workspacepath__empty_object_response__instance_is_created():
    objects = {}
    workspace_path = WorkspacePath.from_api_response(objects)


def test__get_report_writer__junitxmlreportwriter__valid_instance():
    writer = nutter_api.get_report_writer('JunitXMLReportWriter')

    assert isinstance(writer, JunitXMLReportWriter)


def test__get_report_writer__tagsreportwriter__valid_instance():
    writer = nutter_api.get_report_writer('TagsReportWriter')

    assert isinstance(writer, TagsReportWriter)


def test__list_tests__twotest__okay(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/mynotebook'), (ObjectType.NOTEBOOK, '/test_mynotebook'),
         (ObjectType.NOTEBOOK, '/mynotebook_test')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/")

    assert len(tests) == 2
    assert tests[0] == TestNotebook('test_mynotebook', '/test_mynotebook')
    assert tests[1] == TestNotebook('mynotebook_test', '/mynotebook_test')


def test__list_tests__twotest_in_folder__okay(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/folder/mynotebook'), (ObjectType.NOTEBOOK, '/folder/test_mynotebook'),
         (ObjectType.NOTEBOOK, '/folder/mynotebook_test')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/folder")

    assert len(tests) == 2
    assert tests[0] == TestNotebook(
        'test_mynotebook', '/folder/test_mynotebook')
    assert tests[1] == TestNotebook(
        'mynotebook_test', '/folder/mynotebook_test')


def test__list_tests__twotest_uppercase_name__okay(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/mynotebook'), (ObjectType.NOTEBOOK, '/TEST_mynote'), (ObjectType.NOTEBOOK, '/mynote_TEST')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/")

    assert len(tests) == 2
    assert tests == [TestNotebook('TEST_mynote', '/TEST_mynote'),
                     TestNotebook('mynote_TEST', '/mynote_TEST')]


def test__list_tests__nutterstatusevents_testlisting_sequence_is_fired(mocker):
    event_handler = TestEventHandler()
    nutter = _get_nutter(mocker, event_handler)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/mynotebook'), (ObjectType.NOTEBOOK, '/TEST_mynote'), (ObjectType.NOTEBOOK, '/mynote_TEST')])

    nutter.dbclient.list_objects.return_value = workspace_path_1

    tests = nutter.list_tests("/")
    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListing

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListingResults
    assert status_event.data == 2


def test__list_tests_recursively__1test1dir2test__3_tests(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/test_1'), (ObjectType.DIRECTORY, '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/p/test_1'), (ObjectType.NOTEBOOK, '/p/2_test')])

    nutter.dbclient.list_objects.side_effect = [workspace_path_1, workspace_path_2]

    tests = nutter.list_tests("/", True)

    expected = [TestNotebook('test_1', '/test_1'),
                TestNotebook('test_1', '/p/test_1'),
                TestNotebook('2_test', '/p/2_test')]
    assert expected == tests
    assert nutter.dbclient.list_objects.call_count == 2


def test__list_tests_recursively__2test1dir2test__4_tests(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/test_1'), (ObjectType.NOTEBOOK, '/3_test'), (ObjectType.DIRECTORY, '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/p/test_1'), (ObjectType.NOTEBOOK, '/p/test_2')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2]

    tests = nutter.list_tests("/", True)
    print(tests)
    expected = [TestNotebook('test_1', '/test_1'),
                TestNotebook('3_test', '/3_test'),
                TestNotebook('test_1', '/p/test_1'),
                TestNotebook('test_2', '/p/test_2')]

    assert expected == tests
    assert nutter.dbclient.list_objects.call_count == 2


def test__list_tests_recursively__1test1test1dir1dir__2_test(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/test_1'), (ObjectType.NOTEBOOK, '/2_test'), (ObjectType.DIRECTORY, '/p')])
    workspace_path_2 = _get_workspacepathobject([(ObjectType.DIRECTORY, '/p/c')])
    workspace_path_3 = _get_workspacepathobject([])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2, workspace_path_3]

    tests = nutter.list_tests("/", True)

    expected = [TestNotebook('test_1', '/test_1'), TestNotebook('2_test', '/2_test')]

    assert expected == tests
    assert nutter.dbclient.list_objects.call_count == 3


def test__list_tests__notest__empty_list(mocker):
    nutter = _get_nutter(mocker)
    dbapi_client = _get_client(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [
        (ObjectType.NOTEBOOK, '/my'), (ObjectType.NOTEBOOK, '/my2')])

    results = nutter.list_tests("/")

    assert len(results) == 0


def test__run_tests__twomatch_three_tests___nutterstatusevents_testlisting_scheduling_execution_sequence_is_fired(
        mocker):
    event_handler = TestEventHandler()
    nutter = _get_nutter(mocker, event_handler)
    test_results = TestResults()
    test_results.append(TestResult('case', True, 10, []))
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', test_results.serialize())
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        ObjectType.NOTEBOOK, '/test_my'), (ObjectType.NOTEBOOK, '/test_abc'), (ObjectType.NOTEBOOK, '/my_test')])

    results = nutter.run_tests("/my*", "cluster")

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecutionRequest
    assert status_event.data == '/my*'

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListing

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListingResults
    assert status_event.data == 3

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestsListingFiltered
    assert status_event.data == 2

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestScheduling
    assert status_event.data == '/test_my'

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestScheduling
    assert status_event.data == '/my_test'

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecuted
    assert status_event.data.success

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecuted
    assert status_event.data.success

    status_event = event_handler.get_item()
    assert status_event.event == NutterStatusEvents.TestExecutionResult
    assert status_event.data  # True if success


def test__run_tests__twomatch__okay(mocker):
    nutter = _get_nutter(mocker)
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [
        (ObjectType.NOTEBOOK, '/test_my'),
        (ObjectType.NOTEBOOK, '/my'),
        (ObjectType.NOTEBOOK, '/my_test')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 2

    result = results[0]
    assert result.task_result_state == 'TERMINATED'

    result = results[1]
    assert result.task_result_state == 'TERMINATED'


def test__run_tests_recursively__2test1dir3test__5_tests(mocker):
    nutter = _get_nutter(mocker)
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)
    nutter.dbclient = dbapi_client

    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/test_1'), (ObjectType.NOTEBOOK, '/2_test'), (ObjectType.DIRECTORY, '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/p/test_1'), (ObjectType.NOTEBOOK, '/p/test_2'), (ObjectType.NOTEBOOK, '/p/3_test')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2]

    tests = nutter.run_tests('/', 'cluster', 120, 1, True)
    assert len(tests) == 5


def test__run_tests_recursively__1dir1dir3test__3_tests(mocker):
    nutter = _get_nutter(mocker)
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)
    nutter.dbclient = dbapi_client

    mocker.patch.object(nutter.dbclient, 'list_objects')

    workspace_path_1 = _get_workspacepathobject(
        [(ObjectType.DIRECTORY, '/p')])
    workspace_path_2 = _get_workspacepathobject(
        [(ObjectType.DIRECTORY, '/c')])
    workspace_path_3 = _get_workspacepathobject(
        [(ObjectType.NOTEBOOK, '/p/c/test_1'), (ObjectType.NOTEBOOK, '/p/c/test_2'), (ObjectType.NOTEBOOK, '/p/c/3_test')])

    nutter.dbclient.list_objects.side_effect = [
        workspace_path_1, workspace_path_2, workspace_path_3]

    tests = nutter.run_tests('/', 'cluster', 120, 1, True)
    assert len(tests) == 3


def test__run_tests__twomatch__is_uppercase__okay(mocker):
    nutter = _get_nutter(mocker)
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        ObjectType.NOTEBOOK, '/TEST_my'), (ObjectType.NOTEBOOK, '/my'), (ObjectType.NOTEBOOK, '/my_TEST')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 2
    assert results[0].task_result_state == 'TERMINATED'


def test__run_tests__nomatch_case_sensitive__okay(mocker):
    nutter = _get_nutter(mocker)
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)

    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        ObjectType.NOTEBOOK, '/test_MY'), (ObjectType.NOTEBOOK, '/my'), (ObjectType.NOTEBOOK, '/MY_test')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 0


def test__run_tests__fourmatches_with_pattern__okay(mocker):
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)

    nutter = _get_nutter(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        ObjectType.NOTEBOOK, '/test_my'), (ObjectType.NOTEBOOK, '/test_my2'), (ObjectType.NOTEBOOK, '/my_test'),
        (ObjectType.NOTEBOOK, '/my3_test')])

    results = nutter.run_tests("/my*", "cluster")

    assert len(results) == 4
    assert results[0].task_result_state == 'TERMINATED'
    assert results[1].task_result_state == 'TERMINATED'
    assert results[2].task_result_state == 'TERMINATED'
    assert results[3].task_result_state == 'TERMINATED'


def test__run_tests__with_invalid_pattern__valueerror(mocker):
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)
    nutter = _get_nutter(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        ObjectType.NOTEBOOK, '/test_my'), (ObjectType.NOTEBOOK, '/test_my2')])

    with pytest.raises(ValueError):
        results = nutter.run_tests("/my/(", "cluster")


def test__run_tests__nomatches__okay(mocker):
    submit_response, run_output = _get_submit_run_response('SUCCESS', 'TERMINATED', '')
    dbapi_client = _get_client_for_execute_notebook(mocker, submit_response, run_output)
    nutter = _get_nutter(mocker)
    nutter.dbclient = dbapi_client
    _mock_dbclient_list_objects(mocker, dbapi_client, [(
        ObjectType.NOTEBOOK, '/test_my'), (ObjectType.NOTEBOOK, '/test_my2'), (ObjectType.NOTEBOOK, '/my_test'),
        (ObjectType.NOTEBOOK, '/my3_test')])

    results = nutter.run_tests("/abc*", "cluster")

    assert len(results) == 0


def test__to_testresults__none_output__none(mocker):
    output = None
    result = nutter_api.to_test_results(output)

    assert result is None


def test__to_testresults__non_pickle_output__none(mocker):
    output = 'NOT A PICKLE'
    result = nutter_api.to_test_results(output)

    assert result is None


def test__to_testresults__pickle_output__testresult(mocker):
    output = TestResults().serialize()
    result = nutter_api.to_test_results(output)

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
    ('a', [TestNotebook("a_test", "/a_test")], 1),
    ('*', [TestNotebook("test_a", "/test_a"), TestNotebook("test_b", "/test_b")], 2),
    ('*', [TestNotebook("a_test", "/a_test"), TestNotebook("b_test", "/b_test")], 2),
    ('b*', [TestNotebook("test_a", "/test_a"), TestNotebook("test_b", "/test_b")], 1),
    ('b*', [TestNotebook("a_test", "/a_test"), TestNotebook("b_test", "/b_test")], 1),
    ('b*', [TestNotebook("test_ba", "/test_ba"), TestNotebook("test_b", "/test_b")], 2),
    ('b*', [TestNotebook("ba_test", "/ba_test"), TestNotebook("b_test", "/b_test")], 2),
    ('c*', [TestNotebook("test_a", "/test_a"), TestNotebook("test_b", "/test_b")], 0),
    ('c*', [TestNotebook("a_test", "/a_test"), TestNotebook("b_test", "/b_test")], 0),
]


@pytest.mark.parametrize('pattern, list_results, expected_count', filter_patterns)
def test__filter_by_pattern__valid_scenarios__result_len_is_expected_count(pattern, list_results,
                                                                           expected_count):
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
    run_info = Run(
        tasks=[
            RunTask(task_key="test_task",
                    notebook_task=NotebookTask("/mynotebook"),
                    run_id=2,
                    state=RunState(life_cycle_state=getattr(RunLifeCycleState, life_cycle_state),
                                   result_state=getattr(RunResultState, result_state),
                                   state_message=""))
        ],
        run_id=1,
        run_page_url="https://westus2.azuredatabricks.net/?o=14702dasda6094293890#job/4/run/1",
        state=RunState(life_cycle_state=getattr(RunLifeCycleState, life_cycle_state),
                       result_state=getattr(RunResultState, result_state),
                       state_message=""),
    )
    notebook_output = RunOutput(notebook_output=NotebookOutput(result=result, truncated=False))
    return run_info, notebook_output


def _get_client_for_execute_notebook(mocker, run_info, run_output):
    db = _get_client(mocker)
    mocker.patch.object(db.dbclient.jobs, 'submit_and_wait')
    db.dbclient.jobs.submit_and_wait.return_value = run_info
    mocker.patch.object(db.dbclient.jobs, 'get_run_output')
    db.dbclient.jobs.get_run_output.return_value = run_output

    return db


def _get_client(mocker):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    return DatabricksAPIClient()


def _get_nutter(mocker, event_handler=None):
    mocker.patch.dict(os.environ, {'DATABRICKS_HOST': 'myhost'})
    mocker.patch.dict(os.environ, {'DATABRICKS_TOKEN': 'mytoken'})

    return Nutter(event_handler)


def _mock_dbclient_list_objects(mocker, dbclient, objects):
    mocker.patch.object(dbclient, 'list_objects')

    workspace_objects = _get_workspacepathobject(objects)
    dbclient.list_objects.return_value = workspace_objects


def _get_workspacepathobject(objects):
    objects_list = [ObjectInfo(path=obj[1], language=Language.PYTHON, object_type=obj[0])
                    for obj in objects]
    return WorkspacePath.from_api_response(objects_list)


class TestEventHandler(EventHandler):
    __test__ = False  # Tell pytest this is not a test class
    
    def __init__(self):
        self._queue = None
        super().__init__()

    def handle(self, queue):
        self._queue = queue

    def get_item(self):
        item = self._queue.get()
        self._queue.task_done()
        return item
