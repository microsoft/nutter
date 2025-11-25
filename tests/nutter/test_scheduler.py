"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import common.scheduler as scheduler
import time
import datetime


def test__run_and_wait__1_function_1_worker_exception__result_is_none_and_exception():
    func_scheduler = scheduler.get_scheduler(1)
    func_scheduler.add_function(__raise_it, Exception)
    results = func_scheduler.run_and_wait()
    assert len(results) == 1
    assert results[0].func_result is None
    assert isinstance(results[0].exception, Exception)


params = [
    (1, 1, 'this'),
    (1, 2, 'this'),
    (2, 2, 'this'),
    (2, 10, 'this'),
    (2, 2, {'this': 'this'}),
    (2, 2, ('this', 'that')),
]


@pytest.mark.parametrize('num_of_funcs, num_of_workers, func_return_value', params)
def test__run_and_wait__X_functions_X_workers_x_value__results_are_okay(num_of_funcs,
                                                                        num_of_workers,
                                                                        func_return_value):
    func_scheduler = scheduler.get_scheduler(num_of_workers)

    for i in range(0, num_of_funcs):
        func_scheduler.add_function(__get_back, func_return_value)

    results = func_scheduler.run_and_wait()
    assert len(results) == num_of_funcs

    for result in results:
        assert result.func_result == func_return_value


def test__run_and_wait__3_function_1_worker__in_sequence():
    func_scheduler = scheduler.get_scheduler(1)
    value1 = 'this1'
    func_scheduler.add_function(__get_back, value1)
    value2 = 'this2'
    func_scheduler.add_function(__get_back, value2)
    value3 = 'this3'
    func_scheduler.add_function(__get_back, value3)
    results = func_scheduler.run_and_wait()
    assert len(results) == 3
    assert results[0].func_result == value1
    assert results[1].func_result == value2
    assert results[2].func_result == value3


def test__run_and_wait__2_functions_1_worker_500ms_delay__sequential_duration():
    func_scheduler = scheduler.get_scheduler(1)
    wait_time = .500
    func_scheduler.add_function(__wait, wait_time)
    func_scheduler.add_function(__wait, wait_time)
    start = time.time()
    results = func_scheduler.run_and_wait()
    end = time.time()
    delay = int(end - start)
    assert delay >= 2 * wait_time


def test__run_and_wait__3_functions_3_worker_500ms_delay__less_than_sequential_duration():
    func_scheduler = scheduler.get_scheduler(1)
    wait_time = .500
    func_scheduler.add_function(__wait, wait_time)
    func_scheduler.add_function(__wait, wait_time)
    func_scheduler.add_function(__wait, wait_time)
    start = time.time()
    results = func_scheduler.run_and_wait()
    end = time.time()
    delay = int(end - start)
    assert delay < 3 * wait_time


def __get_back(this):
    return this


def __raise_it(exception):
    raise exception


def __wait(time_to_wait):
    time.sleep(time_to_wait)
