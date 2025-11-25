"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import logging
from abc import ABCMeta
from common.testresult import TestResults
from .fixtureloader import FixtureLoader
from common.testexecresults import TestExecResults
from collections import OrderedDict


def tag(the_tag):
    def tag_decorator(function):
        if not isinstance(the_tag, list) and not isinstance(the_tag, str):
            raise ValueError("the_tag must be a string or a list")
        if not str.startswith(function.__name__, "run_"):
            raise ValueError("a tag may only decorate a run_ method")

        function.tag = the_tag
        return function

    return tag_decorator


class NutterFixture(object):
    """
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self.data_loader = FixtureLoader()
        self.test_results = TestResults()
        self._logger = logging.getLogger('NutterRunner')

    def execute_tests(self):
        self.__load_fixture()

        if len(self.__test_case_dict) > 0 and self.__has_method("before_all"):
            logging.debug('Running before_all()')
            self.before_all()

        for key, value in self.__test_case_dict.items():
            logging.debug(f'Running test: {key}')
            test_result = value.execute_test()
            logging.debug(f'Completed running test: {key}')
            self.test_results.append(test_result)

        if len(self.__test_case_dict) > 0 and self.__has_method("after_all"):
            logging.debug('Running after_all()')
            self.after_all()

        return TestExecResults(self.test_results)

    def __load_fixture(self):
        if hasattr(self, 'data_loader') is False:
            msg = """ If you have an __init__ method in your test class.
                      Make sure you make a call to initialize the parent class.
                      For example: super().__init__() """
            raise InitializationException(msg)

        test_case_dict = self.data_loader.load_fixture(self)
        if test_case_dict is None:
            logging.fatal("Invalid Test Fixture")
            raise InvalidTestFixtureException("Invalid Test Fixture")
        self.__test_case_dict = OrderedDict(sorted(test_case_dict.items(), key=lambda t: t[0]))

        logging.debug(f"Found {len(test_case_dict)} test cases")
        for key, value in self.__test_case_dict.items():
            logging.debug(f'Test Case: {key}')

    def __has_method(self, method_name):
        method = getattr(self, method_name, None)
        if callable(method):
            return True
        return False


class InvalidTestFixtureException(Exception):
    def __init__(self, message):
        super().__init__(message)


class InitializationException(Exception):
    def __init__(self, message):
        super().__init__(message)
