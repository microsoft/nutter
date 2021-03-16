"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from .apiclientresults import ExecuteNotebookResult, NotebookOutputResult
from .resultreports import JunitXMLReportWriter
from .resultsview import RunCommandResultsView
from .testresult import TestResults


class TestExecResults():
    def __init__(self, test_results):
        if not isinstance(test_results, TestResults):
            raise TypeError("test_results must be of type TestResults")
        self.test_results = test_results
        self.runcommand_results_view = RunCommandResultsView()

    def to_string(self):
        notebook_path = ""
        notebook_result = self.get_ExecuteNotebookResult(
            notebook_path, self.test_results)
        self.runcommand_results_view.add_exec_result(notebook_result)
        view = self.runcommand_results_view.get_view()
        return view

    def exit(self, dbutils):
        dbutils.notebook.exit(self.test_results.serialize())

    def get_ExecuteNotebookResult(self, notebook_path, test_results):
        notebook_result = NotebookOutputResult(
            'N/A', None, test_results)

        return ExecuteNotebookResult('N/A', 'N/A', notebook_result, 'N/A')

    def write_junit_xml_report_to_dbfs(self, notebook_path, dbfs_report_path):
        junit_xml_report_writer = JunitXMLReportWriter()
        junit_xml_report_writer.add_result(notebook_path, self.test_results)
        junit_xml_report_writer.write_to_dbfs(dbfs_report_path)
        return dbfs_report_path

