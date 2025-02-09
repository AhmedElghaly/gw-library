
import threading

from ttgwlib.events.event import Event, EventType


class TimeEvent(Event):
    """ Class for time related event.

    :param evt_type: Event Type.
    :type evt_type: :class: `events.event.EventType`
    :param data: Related event data.node
    :type data: dict
    :param timeout: time before executing the event.
    :type node: integer
    """
    def __init__(self, event_type, data, timeout, gw):
        super().__init__(event_type, data, gw)
        self.timeout = timeout
        self.start()

    def start(self):
        self.timer = threading.Timer(self.timeout,
            self.gw.event_handler.add_event, [self])
        self.timer.start()

    def cancel(self):
        self.timer.cancel()

    def restart(self):
        self.cancel()
        self.start()


class ConfigTimeout(TimeEvent):
    def __init__(self, timeout, node, gw):
        self.node = node
        data = {}
        super().__init__(EventType.CONFIGURATION_TIMEOUT, data, timeout, gw)


class ScanTimeout(TimeEvent):
    def __init__(self, timeout, gw):
        data = {}
        super().__init__(EventType.SCAN_TIMEOUT, data, timeout, gw)


class TaskTimeout(TimeEvent):
    def __init__(self, node, timeout, gw):
        self.node = node
        data = {}
        super().__init__(EventType.TASK_TIMEOUT, data, timeout, gw)
