"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import base64
import gzip
import zlib
import jsonpickle

from py4j.protocol import Py4JJavaError

from .serializabledata import SerializableData


def get_test_results():
    return TestResults()


class TestResults(SerializableData):
    __test__ = False  # Tell pytest this is not a test class
    
    def __str__(self) -> str:
        return jsonpickle.encode(self)

    def __init__(self):
        self.results = []
        self.test_cases = 0
        self.num_failures = 0
        self.total_execution_time = 0

    def append(self, test_result):
        if not isinstance(test_result, TestResult):
            raise TypeError("Can only append TestResult to TestResults")

        self.results.append(test_result)
        self.test_cases = self.test_cases + 1
        if not test_result.passed:
            self.num_failures = self.num_failures + 1

        total_execution_time = self.total_execution_time + test_result.execution_time
        self.total_execution_time = total_execution_time

    @staticmethod
    def serialize_object(obj):
        bin_data = zlib.compress(bytes(jsonpickle.encode(obj), 'utf-8'))
        return str(base64.encodebytes(bin_data), "utf-8")

    def serialize(self):
        for i in self.results:
            if isinstance(i.exception, Py4JJavaError):
                i.exception = Exception(str(i.exception))
        return self.serialize_object(self)

    def deserialize(self, pickle_string):
        bin_str = pickle_string.encode("utf-8")
        decoded_bin_data = base64.decodebytes(bin_str)
        return jsonpickle.decode(zlib.decompress(decoded_bin_data))

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
            if item == expected_item:
                return True

        return False


class TestResult:
    __test__ = False  # Tell pytest this is not a test class
    
    def __init__(self, test_name, passed, execution_time, tags, exception=None, stack_trace=""):
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
