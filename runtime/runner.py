"""
Copyright (c) Microsoft Corporation.

Licensed under the MIT license.
"""

import common.scheduler as scheduler
from common.testexecresults import TestExecResults
from common.testresult import TestResults

from runtime.nutterfixture import NutterFixture


class NutterFixtureParallelRunner(object):
    """Helper class to execute tests in parallel."""

    def __init__(self, tests, num_of_workers=1):
        """Initialize the runner.

        Args:
            tests (list): the list of tests to execute.
            num_of_workers (int): number of parallel workers.
        """
        for i in tests:
            if not isinstance(i, NutterFixture):
                raise TypeError("tests elements must be of type NutterFixture")
        self.tests = tests
        self.num_of_workers = num_of_workers

    def execute_tests(self):
        """Execute the tests."""
        sched = scheduler.get_scheduler(self.num_of_workers)

        for i in self.tests:
            sched.add_function(i.execute_tests)

        results = sched.run_and_wait()

        return self._collect_results(results)

    def _collect_results(self, results):
        """Collect all results in a single TestExecResults object."""
        all_results = TestResults()

        for funcres in results:
            if funcres.func_result is not None:
                for testres in funcres.func_result.test_results.results:
                    all_results.append(funcres.func_result.test_results.results)

        return TestExecResults(all_results)
