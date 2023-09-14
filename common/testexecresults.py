"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from .apiclientresults import ExecuteNotebookResult, NotebookOutputResult
from .resultsview import RunCommandResultsView
from .testresult import TestResults

import matplotlib.pyplot as plt
import numpy as np


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

    def plot_pie_chart(self, title=None, legend=False, size=5):
        """
        Plot a pie chart representing the distribution of test cases between 'Passed' and 'Failed' categories.

        Parameters:
        - title (str, optional): Title for the pie chart.
        - legend (bool, optional): Whether to display a legend.
        - size (int, optional): Size of the pie chart.

        This method accepts three parameters:
        1. title (str, optional): Title for the pie chart.
        2. legend (bool, optional): Set to True to display a legend; False to hide it.
        3. size (int, optional): Size of the pie chart (both width and height).

        Note: The pie chart is based on the test results in the 'self.test_results' attribute.
        """
        pass_fail_count = self.test_results.get_counts()
        total_testcases = sum(pass_fail_count)

        plt.figure(figsize=(size, size))
        plt.pie(np.array(pass_fail_count), labels=["Passed", "Failed"],
                autopct=lambda p: '{:.0f}'.format(p * total_testcases / 100).replace('0', ''),
                shadow=True, colors=["#4CAF50", "red"])
        if legend:
            plt.legend(title="Test Result", bbox_to_anchor=(0.95, 0.5), bbox_transform=plt.gcf().transFigure,
                       loc="lower right")
        if title is not None:
            plt.title(title, fontweight='bold')
        plt.show()
