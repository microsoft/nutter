"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from .pickleserializable import PickleSerializable
import pickle
import base64

def get_test_results():
    return TestResults()

class TestResults(PickleSerializable):
    def __init__(self):
        self.results = []
        self.test_cases = 0
        self.num_failures = 0
        self.total_execution_time = 0

    def append(self, testresult):
        if not isinstance(testresult, TestResult):
            raise TypeError("Can only append TestResult to TestResults")

        self.results.append(testresult)
        self.test_cases = self.test_cases + 1
        if (not testresult.passed):
            self.num_failures = self.num_failures + 1

        total_execution_time = self.total_execution_time + testresult.execution_time
        self.total_execution_time = total_execution_time

    def serialize(self):
        bin_data = pickle.dumps(self)
        return str(base64.encodebytes(bin_data), "utf-8")

    def deserialize(self, pickle_string):
        bin_str = pickle_string.encode("utf-8")
        decoded_bin_data = base64.decodebytes(bin_str)
        return pickle.loads(decoded_bin_data)

    def passed(self):
        for item in self.results:
            if not item.passed:
                return False
        return True

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        if len(self.results) != len(other.results):
            return False
        for item in other.results:
            if not self.__item_in_list_equalto(item):
                return False

        return True

    def __item_in_list_equalto(self, expected_item):
        for item in self.results:
            if (item == expected_item):
                return True

        return False

class TestResult:
    def __init__(self, test_name, passed,
                 execution_time, tags, exception=None, stack_trace=""):

        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        self.passed = passed
        self.exception = exception
        self.stack_trace = stack_trace
        self.test_name = test_name
        self.execution_time = execution_time
        self.tags = tags

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.test_name == other.test_name \
                and self.passed == other.passed \
                and type(self.exception) == type(other.exception) \
                and str(self.exception) == str(other.exception)

        return False
