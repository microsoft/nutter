"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import os
import time
import traceback
from common.testresult import TestResult


def get_testcase(test_name):

    tc = TestCase(test_name)

    return tc


class TestCase():
    ERROR_MESSAGE_RUN_MISSING = """ TestCase does not contain a run function.
                                      Please pass a function to set_run"""
    ERROR_MESSAGE_ASSERTION_MISSING = """ TestCase does not contain an assertion function.
                                            Please pass a function to set_assertion """

    def __init__(self, test_name):
        self.test_name = test_name
        self.before = None
        self.__before_set = False
        self.run = None
        self.assertion = None
        self.after = None
        self.__after_set = False
        self.invalid_message = ""
        self.tags = []

    def set_before(self, before):
        self.before = before
        self.__before_set = True

    def set_run(self, run):
        self.run = run

    def set_assertion(self, assertion):
        self.assertion = assertion

    def set_after(self, after):
        self.after = after
        self.__after_set = True

    def execute_test(self):
        start_time = time.perf_counter()
        try:
            if hasattr(self.run, "tag"):
                if isinstance(self.run.tag, list):
                    self.tags.extend(self.run.tag)
                else:
                    self.tags.append(self.run.tag)
            if not self.is_valid():
                raise NoTestCasesFoundError(
                    "Both a run and an assertion are required for every test")
            if self.__before_set and self.before is not None:
                self.before()
            self.run()
            self.assertion()
            if self.__after_set and self.after is not None:
                self.after()

        except Exception as exc:
            return TestResult(self.test_name, False,
                              self.__get_elapsed_time(start_time), self.tags,
                              exc, traceback.format_exc())

        return TestResult(self.test_name, True,
                          self.__get_elapsed_time(start_time), self.tags, None)

    def is_valid(self):
        is_valid = True

        if self.run is None:
            self.__add_message_to_error(self.ERROR_MESSAGE_RUN_MISSING)
            is_valid = False

        if self.assertion is None:
            self.__add_message_to_error(self.ERROR_MESSAGE_ASSERTION_MISSING)
            is_valid = False

        return is_valid

    def __get_elapsed_time(self, start_time):
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        return elapsed_time

    def __add_message_to_error(self, message):
        if self.invalid_message:
            self.invalid_message += os.linesep

        self.invalid_message += message

    def get_invalid_message(self):
        self.is_valid()

        return self.invalid_message


class NoTestCasesFoundError(Exception):
    pass
