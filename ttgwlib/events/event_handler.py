import queue
import logging
import threading

from ttgwlib.events.event import EventType

class EventHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.handler_list = []
        self.handler_list_lock = threading.RLock()

        self.event_queue = queue.Queue()
        self.running = True
        threading.Thread(target=self.process_packets, name='EvtHandler').start()

    def process_packets(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
            except queue.Empty:
                continue

            if event.event_type in (EventType.WAKE_NOTIFY,
                    EventType.WAKE_RESET, EventType.TASK_TIMEOUT,
                    EventType.CONFIGURATION_TIMEOUT):
                node = event.node
                self.logger.debug(f'Event: {event.event_type.name}, '
                    + f'Node: ({node.mac.hex()}, {node.unicast_addr})')
            else:
                if (event.event_type == EventType.RSP_EVENT
                        or event.event_type == EventType.RSP_SEND
                        or event.event_type == EventType.MESH_TX_COMPLETE
                        or event.event_type == EventType.TRANSPORT_FR_DATA):
                    self.logger.log(9, f'Event: {event.event_type.name}')
                else:
                    self.logger.log(9, f'Event: {event.event_type.name}')
# pylint: disable=bare-except
            try:
                with self.handler_list_lock:
                    for handler in self.handler_list:
                        handler(event)
            except:
                self.logger.exception("Event handler error")
# pylint: enable=bare-except

    def add_event(self, event):
        self.event_queue.put(event)

    def add_handler(self, handler):
        with self.handler_list_lock:
            if handler not in self.handler_list:
                self.handler_list.append(handler)

    def remove_handler(self, handler):
        with self.handler_list_lock:
            if handler in self.handler_list:
                self.handler_list.remove(handler)

    def stop(self):
        self.running = False
