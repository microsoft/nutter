"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

from abc import abstractmethod, ABC
from queue import Queue
from threading import Thread
from datetime import datetime
from enum import Enum
import logging


class StatusEventsHandler(object):
    def __init__(self, handler):
        self._event_queue = Queue()
        self._processor = Processor(handler, self._event_queue, )

        self._processor.daemon = True
        self._processor.start()

    def add_event(self, event, data):
        self._event_queue.put(StatusEvent(event, data))

    def wait(self):
        self._event_queue.join()


class StatusEvent(object):
    def __init__(self, event, data):
        if not isinstance(event, Enum):
            raise ValueError('Invalid event. Must be an Enum')

        self.timestamp = datetime.utcnow()
        self.event = event
        self.data = data


class EventHandler(ABC):

    @abstractmethod
    def handle(self, queue):
        pass


class Processor(Thread):
    def __init__(self, handler, event_queue):
        self._handler = handler
        self._event_queue = event_queue
        Thread.__init__(self)

    def run(self):
        logging.debug("Starting handler..")
        self._handler.handle(self._event_queue)
