"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from .testcase import TestCase


def get_fixture_loader():
    loader = FixtureLoader()
    return loader


class FixtureLoader():
    def __init__(self):
        self.__test_case_dictionary = {}
        pass

    def load_fixture(self, nutter_fixture):
        if nutter_fixture is None:
            raise ValueError("Must pass NutterFixture")

        all_attributes = dir(nutter_fixture)
        for attribute in all_attributes:
            is_test_method = self.__is_test_method(attribute)
            if is_test_method:
                test_full_name = attribute
                test_name = self.__get_test_name(attribute)
                func = getattr(nutter_fixture, test_full_name)
                if func is None:
                    continue

                if test_name == "before_all" or test_name == "after_all":
                    continue

                test_case = None
                if test_name in self.__test_case_dictionary:
                    test_case = self.__test_case_dictionary[test_name]

                if test_case is None:
                    test_case = TestCase(test_name)

                test_case = self.__set_method(test_case, test_full_name, func)

                self.__test_case_dictionary[test_name] = test_case

        return self.__test_case_dictionary

    @staticmethod
    def __is_test_method(attribute):
        if attribute.startswith("before_") or \
                attribute.startswith("run_") or \
                attribute.startswith("assertion_") or \
                attribute.startswith("after_"):
            return True
        return False

    @staticmethod
    def __set_method(case, name, func):
        if name.startswith("before_"):
            case.set_before(func)
            return case
        if name.startswith("run_"):
            case.set_run(func)
            return case
        if name.startswith("assertion_"):
            case.set_assertion(func)
            return case
        if name.startswith("after_"):
            case.set_after(func)
            return case

        return case

    def __get_test_name(self, full_name):
        if full_name == "before_all" or full_name == "after_all":
            return full_name

        name = self.__remove_prefix(full_name, "before_")
        name = self.__remove_prefix(name, "run_")
        name = self.__remove_prefix(name, "assertion_")
        name = self.__remove_prefix(name, "after_")

        return name

    @staticmethod
    def __remove_prefix(text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text
