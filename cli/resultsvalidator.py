"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from common.apiclientresults import ExecuteNotebookResult
from common.testresult import TestResults
import logging


class ExecutionResultsValidator(object):
    def validate(self, results):
        if not isinstance(results, list):
            raise ValueError("Invalid results. Expected a list")

        for result in results:
            self._validate_result(result)

    def _validate_result(self, result):
        if not isinstance(result, ExecuteNotebookResult):
            raise ValueError("Expected ExecuteNotebookResult")
        if result.is_error:
            msg = f""" The job is not in a successfull terminal state.
                       Life cycle state:{result.task_result_state} """
            raise JobExecutionFailureException(message=msg)
        if result.notebook_result.is_error:
            msg = f'The notebook failed. result state: {result.notebook_result.result_state}'
            raise NotebookExecutionFailureException(message=msg)

        self._validate_test_results(result.notebook_result.exit_output)

    @staticmethod
    def _validate_test_results(exit_output):
        test_results = None
        try:
            test_results = TestResults().deserialize(exit_output)
        except Exception as ex:
            logging.debug(ex)
            msg = f""" The Notebook exit output value is invalid or missing.
                       Additional info: {ex} """
            raise InvalidNotebookOutputException(msg)

        for test_result in test_results.results:
            if not test_result.passed:
                msg = f'The Test Case: {test_result.test_name} failed.'
                raise TestCaseFailureException(msg)


class TestCaseFailureException(Exception):
    __test__ = False  # Tell pytest this is not a test class
    
    def __init__(self, message):
        super().__init__(message)


class JobExecutionFailureException(Exception):
    def __init__(self, message):
        super().__init__(message)


class NotebookExecutionFailureException(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidNotebookOutputException(Exception):
    def __init__(self, message):
        super().__init__(message)
