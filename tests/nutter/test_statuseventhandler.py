"""
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

import pytest
import enum
from common.statuseventhandler import StatusEventsHandler, EventHandler, StatusEvent

def test__add_event_and_wait__1_event__handler_receives_it():
    test_handler = TestEventHandler()
    status_handler = StatusEventsHandler(test_handler)

    status_handler.add_event(TestStatusEvent.AnEvent, 'added')
    item = test_handler.get_item()
    status_handler.wait()

    assert item.event == TestStatusEvent.AnEvent
    assert item.data == 'added'

def test__add_event_and_wait__2_event2__handler_receives_them():
    test_handler = TestEventHandler()
    status_handler = StatusEventsHandler(test_handler)

    status_handler.add_event(TestStatusEvent.AnEvent, 'added')
    status_handler.add_event(TestStatusEvent.AnEvent, 'added')
    item = test_handler.get_item()
    item2 = test_handler.get_item()
    status_handler.wait()

    assert item.event == TestStatusEvent.AnEvent
    assert item.data == 'added'

    assert item2.event == TestStatusEvent.AnEvent
    assert item2.data == 'added'

class TestEventHandler(EventHandler):
    def __init__(self):
        self._queue = None
        super().__init__()

    def handle(self, queue):
        self._queue = queue

    def get_item(self):
        item = self._queue.get()
        self._queue.task_done()
        return item

class TestStatusEvent(enum.Enum):
    AnEvent = 1