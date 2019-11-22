"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""
import logging
from abc import abstractmethod, ABCMeta
from .apiclientresults import ExecuteNotebookResult
from .testresult import TestResults, TestResult
from .stringwriter import StringWriter
from .api import TestNotebook


def get_run_results_views(exec_results):
    if not isinstance(exec_results, list):
        raise ValueError("Expected a List")

    results_view = RunCommandResultsView()
    for exec_result in exec_results:
        results_view.add_exec_result(exec_result)

    return results_view


def get_list_results_view(list_results):
    return ListCommandResultsView(list_results)


def print_results_view(results_view):
    if not isinstance(results_view, ResultsView):
        raise ValueError("Expected ResultsView")

    results_view.print()

    print("Total: {} \n".format(results_view.total))


class ResultsView():
    __metaclass__ = ABCMeta

    def print(self):
        print(self.get_view())

    @abstractmethod
    def get_view(self):
        pass

    @abstractmethod
    def total(self):
        pass


class ListCommandResultsView(ResultsView):
    def __init__(self, listresults):
        if not isinstance(listresults, list):
            raise ValueError("Expected a a list of TestNotebook()")
        self.list_results = [ListCommandResultView.from_test_notebook(test_notebook)
                             for test_notebook in listresults]

        super().__init__()

    def get_view(self):
        writer = StringWriter()
        writer.write_line('{}'.format('\nTests Found'))
        writer.write_line('-' * 55)
        for list_result in self.list_results:
            writer.write(list_result.get_view())

        writer.write_line('-' * 55)

        return writer.to_string()

    @property
    def total(self):
        return len(self.list_results)


class ListCommandResultView(ResultsView):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        super().__init__()

    @classmethod
    def from_test_notebook(cls, test_notebook):
        if not isinstance(test_notebook, TestNotebook):
            raise ValueError('Expected an instance of TestNotebook')
        return cls(test_notebook.name, test_notebook.path)

    def get_view(self):
        return "Name:\t{}\nPath:\t{}\n\n".format(self.name, self.path)

    @property
    def total(self):
        return 1


class RunCommandResultsView(ResultsView):
    def __init__(self):
        self.run_results = []
        super().__init__()

    def add_exec_result(self, result):
        if not isinstance(result, ExecuteNotebookResult):
            raise ValueError("Expected ExecuteNotebookResult")
        self.run_results.append(RunCommandResultView(result))

    def get_view(self):
        writer = StringWriter()
        writer.write('\n')
        for run_result in self.run_results:
            writer.write(run_result.get_view())
            writer.write_line('=' * 60)

        return writer.to_string()

    @property
    def total(self):
        return len(self.run_results)


class RunCommandResultView(ResultsView):
    def __init__(self, result):

        if not isinstance(result, ExecuteNotebookResult):
            raise ValueError("Expected ExecuteNotebookResult")

        self.notebook_path = result.notebook_path
        self.task_result_state = result.task_result_state
        self.notebook_result_state = result.notebook_result.result_state
        self.notebook_run_page_url = result.notebook_run_page_url

        self.raw_notebook_output = result.notebook_result.exit_output
        t_results = self._get_test_results(result)
        self.test_cases_views = []
        if t_results is not None:
            for t_result in t_results.results:
                self.test_cases_views.append(TestCaseResultView(t_result))

        super().__init__()

    def _get_test_results(self, result):
        if result.notebook_result.is_run_from_notebook:
            return result.notebook_result.nutter_test_results

        return self.__to_testresults(result.notebook_result.exit_output)

    def get_view(self):
        sw = StringWriter()
        sw.write_line("Notebook: {} - Lifecycle State: {}, Result: {}".format(
            self.notebook_path, self.task_result_state, self.notebook_result_state))
        sw.write_line('Run Page URL: {}'.format(self.notebook_run_page_url))

        sw.write_line("=" * 60)

        if len(self.test_cases_views) == 0:
            sw.write_line("No test cases were returned.")
            sw.write_line("Notebook output: {}".format(
                self.raw_notebook_output))
            sw.write_line("=" * 60)
            return sw.to_string()

        if len(self.failing_tests) > 0:
            sw.write_line("FAILING TESTS")
            sw.write_line("-" * 60)

            for tc_view in self.failing_tests:
                sw.write(tc_view.get_view())

            sw.write_line("")
            sw.write_line("")

        if len(self.passing_tests) > 0:
            sw.write_line("PASSING TESTS")
            sw.write_line("-" * 60)

            for tc_view in self.passing_tests:
                sw.write(tc_view.get_view())

            sw.write_line("")
            sw.write_line("")

        return sw.to_string()

    def __to_testresults(self, exit_output):
        if not exit_output:
            return None
        try:
            return TestResults().deserialize(exit_output)
        except Exception as ex:
            error = 'error while creating result from {}. Error: {}'.format(
                ex, exit_output)
            logging.debug(error)
            return None

    @property
    def total(self):
        return len(self.test_cases_views)

    @property
    def passing_tests(self):
        return list(filter(lambda x: x.passed, self.test_cases_views))

    @property
    def failing_tests(self):
        return list(filter(lambda x: not x.passed, self.test_cases_views))


class TestCaseResultView(ResultsView):
    def __init__(self, nutter_test_results):

        if not isinstance(nutter_test_results, TestResult):
            raise ValueError("Expected TestResult")

        self.test_case = nutter_test_results.test_name
        self.passed = nutter_test_results.passed
        self.exception = nutter_test_results.exception
        self.stack_trace = nutter_test_results.stack_trace
        self.execution_time = nutter_test_results.execution_time

        super().__init__()

    def get_view(self):
        sw = StringWriter()

        time = '{} seconds'.format(self.execution_time)
        sw.write_line('{} ({})'.format(self.test_case, time))

        if (self.passed):
            return sw.to_string()

        sw.write_line("")
        sw.write_line(self.stack_trace)
        sw.write_line("")
        sw.write_line(self.exception.__class__.__name__ + ": " + str(self.exception))

        return sw.to_string()

    @property
    def total(self):
        return 1
