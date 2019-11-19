"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import logging
import sys
from common.api import NutterStatusEvents
from common.statuseventhandler import EventHandler


class ConsoleEventHandler(EventHandler):
    def __init__(self, debug):
        self._debug = debug
        self._listed_tests = 0
        self._filtered_tests = 0
        self._done_tests = 0
        self._scheduled_tests = 0
        super().__init__()

    def handle(self, event_queue):
        while True:
            self._get_and_handle(event_queue)

    def _get_and_handle(self, event_queue):
        try:
            event_instance = event_queue.get()
            if self._debug:
                logging.debug(
                    'Message from queue: {}'.format(event_instance))
                return
            output = self._get_output(event_instance)
            self._print_output(output)
        except Exception as ex:
            print(ex)
            logging.debug(ex)
        finally:
            event_queue.task_done()

    def _print_output(self, output):
        print(output, end='', file=sys.stdout, flush=True)

    def _get_output(self, event_instance):
        event_output = self._get_event_ouput(event_instance)
        if event_output is None:
            return
        return '--> {}\n'.format(event_output)

    def _get_event_ouput(self, event_instance):
        if event_instance.event is NutterStatusEvents.TestsListing:
            return self._handle_testlisting(event_instance)
        if event_instance.event is NutterStatusEvents.TestsListingFiltered:
            return self._handle_testlistingfiltered(event_instance)
        if event_instance.event is NutterStatusEvents.TestsListingResults:
            return self._handle_testlistingresults(event_instance)
        if event_instance.event is NutterStatusEvents.TestScheduling:
            return self._handle_testscheduling(event_instance)
        if event_instance.event is NutterStatusEvents.TestExecuted:
            return self._handle_testsexecuted(event_instance)
        if event_instance.event is NutterStatusEvents.TestExecutionResult:
            return self._handle_testsexecutionresult(event_instance)
        if event_instance.event is NutterStatusEvents.TestExecutionRequest:
            return self._handle_testsexecutionrequest(event_instance)
        return ''

    def _handle_testlisting(self, event):
        return 'Looking for tests in {}'.format(event.data)

    def _handle_testlistingfiltered(self, event):
        self._filtered_tests = event.data
        return '{} tests matched the pattern'.format(self._filtered_tests)

    def _handle_testlistingresults(self, event):
        return '{} tests found'.format(event.data)

    def _handle_testsexecuted(self, event):
        return '{} Success:{} {}'.format(event.data.notebook_path,
                                         event.data.success,
                                         event.data.notebook_run_page_url)

    def _handle_testsexecutionrequest(self, event):
        return 'Execution request: {}'.format(event.data)

    def _handle_testscheduling(self, event):
        num_of_tests = self._num_of_test_to_execute()
        self._scheduled_tests += 1
        return '{} of {} tests scheduled for execution'.format(self._scheduled_tests,
                                                               num_of_tests)

    def _handle_testsexecutionresult(self, event):
        num_of_tests = self._num_of_test_to_execute()
        self._done_tests += 1
        return '{} of {} tests executed'.format(self._done_tests, num_of_tests)

    def _num_of_test_to_execute(self):
        if self._filtered_tests > 0:
            return self._filtered_tests
        return self._listed_tests
