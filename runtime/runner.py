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

    def __init__(self, num_of_workers=1):
        """Initialize the runner.

        Args:
            num_of_workers (int): number of parallel workers.
        """
        self.tests = []
        self.num_of_workers = num_of_workers

    def add_test_fixture(self, fixture):
        """Add a test to the list of tests to run.

        Args:
            fixture (NutterFixture): the test to add.
        """
        if not isinstance(fixture, NutterFixture):
            raise TypeError("fixture must be of type NutterFixture")
        self.tests.append(fixture)

    def execute(self):
        """Execute the tests."""
        sched = scheduler.get_scheduler(self.num_of_workers)

        for i in self.tests:
            sched.add_function(i.execute_tests)

        results = sched.run_and_wait()

        return self._collect_results(results)

    @staticmethod
    def _collect_results(results):
        """Collect all results in a single TestExecResults object."""
        all_results = TestResults()

        for funcres in results:
            if funcres.func_result is not None:
                for testres in funcres.func_result.test_results.results:
                    all_results.append(testres)

        return TestExecResults(all_results)
