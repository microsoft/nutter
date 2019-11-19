"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from abc import abstractmethod, ABCMeta
from .testresult import TestResults
from . import scheduler
from . import apiclient
from .resultreports import JunitXMLReportWriter, TestResultsReportWriter
from .statuseventhandler import StatusEventsHandler

import enum
import logging

import re
import importlib


def get_nutter(event_handler=None):
    return Nutter(event_handler)


def get_junit_writer():
    return JunitXMLReportWriter()


def get_report_writer(writer):
    module = importlib.import_module('common.resultreports')
    report_writer = getattr(module, writer)
    instance = report_writer()
    if isinstance(report_writer, TestResultsReportWriter):
        raise ValueError(
            'The report writer must a class derived from TestResultsReportWriter')
    return instance


def to_testresults(exit_output):
    if not exit_output:
        return None
    try:
        return TestResults().deserialize(exit_output)
    except Exception as ex:
        error = 'error while creating result from {}. Error: {}'.format(
            ex, exit_output)
        logging.debug(error)
        return None


class NutterApi(object):
    """
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def list_tests(self, path, recursive):
        pass

    @abstractmethod
    def run_tests(self, pattern, cluster_id, timeout, max_parallel_tests):
        pass

    @abstractmethod
    def run_test(self, testpath, cluster_id, timeout):
        pass


class Nutter(NutterApi):
    """
    """

    def __init__(self, event_handler=None):
        self.dbclient = apiclient.databricks_client()
        self._events_processor = self._get_status_events_handler(event_handler)
        super().__init__()

    def list_tests(self, path, recursive=False):
        tests = []
        for test in self._list_tests(path, recursive):
            tests.append(test)

        self._add_status_event(
            NutterStatusEvents.TestsListingResults, len(tests))

        return tests

    def run_test(self, testpath, cluster_id, timeout=120):
        self._add_status_event(NutterStatusEvents.TestExecutionRequest, testpath)
        test_notebook = TestNotebook.from_path(testpath)
        if test_notebook is None:
            raise InvalidTestException

        result = self.dbclient.execute_notebook(
            test_notebook.path, cluster_id, timeout=timeout)

        return result

    def run_tests(self, pattern, cluster_id,
                  timeout=120, max_parallel_tests=1, recursive=False):

        self._add_status_event(NutterStatusEvents.TestExecutionRequest, pattern)
        root, pattern_to_match = self._get_root_and_pattern(pattern)

        tests = self.list_tests(root, recursive)

        results = []
        if len(tests) == 0:
            return results

        pattern_matcher = TestNamePatternMatcher(pattern_to_match)
        filtered_notebooks = pattern_matcher.filter_by_pattern(tests)
        self._add_status_event(
            NutterStatusEvents.TestsListingFiltered, len(filtered_notebooks))

        return self._schedule_and_run(
            filtered_notebooks, cluster_id, max_parallel_tests, timeout)

    def events_processor_wait(self):
        if self._events_processor is None:
            return
        self._events_processor.wait()

    def _list_tests(self, path, recursive):
        self._add_status_event(NutterStatusEvents.TestsListing, path)
        workspace_objects = self.dbclient.list_objects(path)

        for notebook in workspace_objects.test_notebooks:
            yield TestNotebook(notebook.name, notebook.path)

        if not recursive:
            return

        for directory in workspace_objects.directories:
            for test in self._list_tests(directory.path, True):
                yield test

    def _get_status_events_handler(self, events_handler):
        if events_handler is None:
            return None
        processor = StatusEventsHandler(events_handler)
        logging.debug('Status events processor created')
        return processor

    def _add_status_event(self, name, status):
        if self._events_processor is None:
            return
        logging.debug('Status event. name:{} status:{}'.format(name, status))

        self._events_processor.add_event(name, status)

    def _get_root_and_pattern(self, pattern):
        segments = pattern.split('/')
        if len(segments) == 0:
            raise ValueError("Invalid pattern. The value must start with /")
        root = '/'.join(segments[:len(segments)-1])

        if root == '':
            root = '/'

        valid_pattern = segments[len(segments)-1]

        return root, valid_pattern

    def _schedule_and_run(self, test_notebooks, cluster_id,
                          max_parallel_tests, timeout):
        func_scheduler = scheduler.get_scheduler(max_parallel_tests)
        for test_notebook in test_notebooks:
            self._add_status_event(
                NutterStatusEvents.TestScheduling, test_notebook.path)
            logging.debug(
                'Scheduling execution of: {}'.format(test_notebook.path))
            func_scheduler.add_function(self._execute_notebook,
                                        test_notebook.path, cluster_id, timeout)
        return self._run_and_await(func_scheduler)

    def _execute_notebook(self, test_notebook_path, cluster_id, timeout):
        result = self.dbclient.execute_notebook(test_notebook_path,
                                                cluster_id, None, timeout)
        self._add_status_event(NutterStatusEvents.TestExecuted,
                               ExecutionResultEventData.from_execution_results(result))
        logging.debug('Executed: {}'.format(test_notebook_path))
        return result

    def _run_and_await(self, func_scheduler):
        logging.debug('Scheduler run and wait.')
        func_results = func_scheduler.run_and_wait()
        return self.__process_func_results(func_results)

    def __process_func_results(self, func_results):
        results = []
        for func_result in func_results:
            self._inspect_result(func_result)
            results.append(func_result.func_result)
        return results

    def _inspect_result(self, func_result):
        logging.debug('Processing function results.')

        self._add_status_event(NutterStatusEvents.TestExecutionResult, '{}'.format(
            func_result.exception is not None))

        if func_result.exception is not None:
            logging.debug('Exception:{}'.format(func_result.exception))
            raise func_result.exception


class TestNotebook(object):
    def __init__(self, name, path):
        if not self._is_valid_test_name(name):
            raise InvalidTestException

        self.name = name
        self.path = path
        self.test_name = name.split("_")[1]

    def __eq__(self, obj):
        is_equal = obj.name == self.name and obj.path == self.path
        return isinstance(obj, TestNotebook) and is_equal

    @classmethod
    def from_path(cls, path):
        name = cls._get_notebook_name_from_path(path)
        if not cls._is_valid_test_name(name):
            return None
        return cls(name, path)

    @classmethod
    def _is_valid_test_name(cls, name):
        if name is None:
            return False

        return name.lower().startswith('test_')

    @classmethod
    def _get_notebook_name_from_path(cls, path):
        segments = path.split('/')
        if len(segments) == 0:
            raise ValueError('Invalid path. Path must start /')
        name = segments[len(segments)-1]
        return name


class TestNamePatternMatcher(object):
    def __init__(self, pattern):
        try:
            # * is an invalid regex in python
            # however, we want to treat it as no filter
            if pattern == '*' or pattern is None or pattern == '':
                self._pattern = None
                return
            re.compile(pattern)
        except re.error as ex:
            logging.debug('Pattern could not be compiled. {}'.format(ex))
            raise ValueError(
                """ The pattern provided is invalid.
                     The pattern must start with an alphanumeric character """)
        self._pattern = pattern

    def filter_by_pattern(self, test_notebooks):
        results = []
        for test_notebook in test_notebooks:
            if self._pattern is None:
                results.append(test_notebook)
                continue

            search_result = re.search(self._pattern, test_notebook.test_name)
            if search_result is not None and search_result.end() > 0:
                results.append(test_notebook)
        return results

class ExecutionResultEventData():
    def __init__(self, notebook_path, success, notebook_run_page_url):
        self.success = success
        self.notebook_path = notebook_path
        self.notebook_run_page_url = notebook_run_page_url

    @classmethod
    def from_execution_results(cls, exec_results):
        notebook_run_page_url = exec_results.notebook_run_page_url
        notebook_path = exec_results.notebook_path
        try:
            success = not exec_results.is_any_error
        except Exception as ex:
            logging.debug("Error while creating the ExecutionResultEventData {}", ex)
            success = False
        finally:
            return cls(notebook_path, success, notebook_run_page_url)


class NutterStatusEvents(enum.Enum):
    TestExecutionRequest = 1
    TestsListing = 2
    TestsListingFiltered = 3
    TestsListingResults = 4
    TestScheduling = 5
    TestExecuted = 6
    TestExecutionResult = 7


class InvalidTestException(Exception):
    pass
