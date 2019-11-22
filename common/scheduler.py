"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import threading
import logging
from threading import Thread
from queue import Queue

def get_scheduler(num_of_workers):
    return Scheduler(num_of_workers)


class Scheduler(object):
    def __init__(self, num_of_workers):
        if num_of_workers < 1 or num_of_workers > 15:
            raise ValueError(
                'Number of workers is invalid. It must be a value bettwen 1 and 15')
        self._num_of_workers = num_of_workers
        self._in_queue = Queue()
        self._out_queue = Queue()

    def add_function(self, function, *args):
        function_exec = FunctionToExecute(function, *args)
        self._in_queue.put(function_exec)

    def run_and_wait(self):
        try:
            logging.debug("Starting workers")
            workers = []
            w = 0
            while w < self._num_of_workers:
                worker = FunctionHandler(self._in_queue, self._out_queue)
                worker.daemon = True
                worker.start()
                workers.append(worker)
                w += 1

            logging.debug("Workers started")
            self._in_queue.join()
            logging.debug("Stopping workers")
            for worker in workers:
                worker.signal_stop()
            self._in_queue.join()

            return self._process_results()

        except Exception as ex:
            logging.critical(ex)
            raise ex

    def _process_results(self):
        results_handler = ResultsHandler(self._out_queue)
        results_handler.daemon = True
        results_handler.start()
        self._out_queue.join()
        results_handler.signal_stop()
        self._out_queue.join()
        return results_handler.func_results


class Worker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._done = threading.Event()

    def set_done(self):
        self._done.set()


class ResultsHandler(Worker):
    def __init__(self, queue):
        super().__init__()
        self._queue = queue
        self.func_results = []

    def signal_stop(self):
        self._queue.put(None)

    def run(self):
        while True:
            try:
                result = self._queue.get()
                if result is None:
                    break
                self.func_results.append(result)
            finally:
                self._queue.task_done()
        self.set_done()
        logging.debug("Results handler is done")


class FunctionHandler(Worker):
    def __init__(self, in_queue, out_queue):
        super().__init__()
        self._in_queue = in_queue
        self._out_queue = out_queue

    def signal_stop(self):
        self._in_queue.put(None)

    def run(self):
        logging.debug("Function Handler Starting")
        while True:
            try:
                function_exe = self._in_queue.get()
                if function_exe is None:
                    logging.debug("Function Handler Stopped")
                    break
                logging.debug('Function Handler: Execute for {}'.format(function_exe))
                result = function_exe.execute()
                logging.debug('Function Handler: Execute called.')
                self._out_queue.put(FunctionResult(result, None))

            except Exception as ex:
                self._out_queue.put(FunctionResult(None, ex))
                logging.debug('Function Handler. Exception in function. Error {} {}'
                              .format(str(ex), ex is None))
            finally:
                self._in_queue.task_done()
        self.set_done()
        logging.debug("Function handler is done")


class FunctionToExecute(object):
    def __init__(self, function, *args):
        self._function = function
        self._args = args

    def execute(self):
        return self._function(*self._args)


class FunctionResult(object):
    def __init__(self, result, exception):
        self.func_result = result
        self.exception = exception
