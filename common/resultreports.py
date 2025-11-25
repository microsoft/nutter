"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from abc import abstractmethod, ABCMeta
from .testresult import TestResults
from junit_xml import TestSuite, TestCase
import datetime
import logging


class TestResultsReportWriter(object):
    """
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def add_result(self, notebook_path, test_result):
        pass

    @abstractmethod
    def to_file(self, path):
        pass

    @abstractmethod
    def has_data(self):
        pass

    @abstractmethod
    def write(self):
        pass

    @staticmethod
    def _validate_add_results(notebook_path, test_result):
        if not isinstance(test_result, TestResults):
            raise ValueError('Expected an instance of TestResults')
        if notebook_path is None or notebook_path == '':
            raise ValueError("Invalid notebook path")


class TagsReportRow(object):
    def __init__(self, notebook_name, test_result):
        self.notebook_name = notebook_name
        self.test_name = test_result.test_name
        self.passed_str = 'PASSED'
        if not test_result.passed:
            self.passed_str = 'FAILED'
        self.duration = test_result.execution_time
        self.tags = self._to_tag_string(test_result.tags)

    @staticmethod
    def _to_tag_string(tags):
        logging.debug(tags)
        if tags is None:
            return ''
        value = ''
        for tag in tags:
            value = value + ' {}'.format(tag)
        return value

    def to_string(self):
        str_value = '{},{},{},{},{}\n'.format(
                    self.tags, self.notebook_name,
                    self.test_name, self.passed_str, self.duration)
        return str_value


class TagsReportWriter(TestResultsReportWriter):
    def __init__(self):
        super().__init__()
        self._rows = []

    def add_result(self, notebook_path, test_result):
        self._validate_add_results(notebook_path, test_result)

        new_rows = [TagsReportRow(notebook_path, test_result)
                    for test_result in test_result.results]
        self._rows.extend(new_rows)

    def has_data(self):
        return len(self._rows) > 0

    def write(self):
        report_name = 'test-nutter-tags.{0:%Y.%m.%d.%H%M%S%f}.txt'.format(
            datetime.datetime.utcnow())
        self.to_file(report_name)

        return report_name

    def to_file(self, path):
        file = open(path, 'w')
        try:
            for row in self._rows:
                file.write(row.to_string())
        finally:
            file.close()


class JunitXMLReportWriter(TestResultsReportWriter):
    def __init__(self):
        super().__init__()
        self.all_test_suites = []

    def add_result(self, notebook_path, test_result):
        self._validate_add_results(notebook_path, test_result)

        t_suite = self._to_junitxml(notebook_path, test_result)
        self.all_test_suites.append(t_suite)

    @staticmethod
    def _to_junitxml(notebook_path, test_result):
        tsuite = TestSuite("nutter")
        for t_result in test_result.results:
            fail_error = None
            tc_result = 'PASSED'
            if not t_result.passed:
                fail_error = 'Exception: {} \n Stack: {}'.format(
                    t_result.exception, t_result.stack_trace)
                tc_result = 'FAILED'

            t_case = TestCase(t_result.test_name,
                              classname=notebook_path,
                              elapsed_sec=t_result.execution_time,
                              stderr=fail_error,
                              stdout=tc_result)

            if tc_result == 'FAILED':
                t_case.add_failure_info(tc_result, fail_error)

            tsuite.test_cases.append(t_case)
        return tsuite

    def has_data(self):
        return len(self.all_test_suites) > 0

    def write(self):
        report_name = 'test-nutter-result.{0:%Y.%m.%d.%H%M%S%f}.xml'.format(
            datetime.datetime.utcnow())
        self.to_file(report_name)

        return report_name

    def to_file(self, path):
        file = open(path, 'w')
        try:
            file.write(TestSuite.to_xml_string(self.all_test_suites))
        finally:
            file.close()
