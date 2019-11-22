"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
from queue import Queue
from cli.eventhandlers import ConsoleEventHandler
from common.api import NutterStatusEvents, ExecutionResultEventData
from common.statuseventhandler import StatusEvent


def test__handle__nutterstatusevents_testslisting__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    path = '/path'
    events = [StatusEvent(NutterStatusEvents.TestsListing, path)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper('Looking for tests in {}'.format(path))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testsexecutionrequest__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    pattern = '/path'
    events = [StatusEvent(NutterStatusEvents.TestExecutionRequest, pattern)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper('Execution request: {}'.format(pattern))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testslistingfiltered__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    num_of_tests = 1
    events = [StatusEvent(
        NutterStatusEvents.TestsListingFiltered, num_of_tests)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper(
        '{} tests matched the pattern'.format(num_of_tests))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testlistingresults__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    num_of_tests = 1
    events = [StatusEvent(
        NutterStatusEvents.TestsListingResults, num_of_tests)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper('{} tests found'.format(num_of_tests))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testscheduling__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    num_of_tests = 1
    console_event_handler._filtered_tests = num_of_tests
    events = [StatusEvent(NutterStatusEvents.TestScheduling, num_of_tests)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper(
        '{} of {} tests scheduled for execution'.format(num_of_tests, num_of_tests))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testsexecutionresult__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    num_of_tests = 1
    done_tests = 1
    console_event_handler._listed_tests = num_of_tests
    events = [StatusEvent(
        NutterStatusEvents.TestExecutionResult, num_of_tests)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper(
        '{} of {} tests executed.'.format(done_tests, num_of_tests))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testsexecutionresult__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    num_of_tests = 1
    done_tests = 1
    console_event_handler._listed_tests = num_of_tests
    events = [StatusEvent(
        NutterStatusEvents.TestExecutionResult, num_of_tests)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper(
        '{} of {} tests executed'.format(done_tests, num_of_tests))
    console_event_handler._print_output.assert_called_with(expected)


def test__handle__nutterstatusevents_testexecuted__output_is_valid(mocker):
    console_event_handler = ConsoleEventHandler(False)
    mocker.patch.object(console_event_handler, '_print_output')
    event_data = ExecutionResultEventData('/my', True, 'http://url')
    events = [StatusEvent(NutterStatusEvents.TestExecuted, event_data)]
    queue = _get_queue_with_events(events)

    console_event_handler._get_and_handle(queue)

    expected = _get_output_wrapper('{} Success:{} {}'.format(
        event_data.notebook_path, event_data.success, event_data.notebook_run_page_url))
    console_event_handler._print_output.assert_called_with(expected)


def _get_output_wrapper(output):
    return '--> {}\n'.format(output)


def _get_queue_with_events(events):
    queue = Queue()
    for event in events:
        queue.put(event)
    return queue
