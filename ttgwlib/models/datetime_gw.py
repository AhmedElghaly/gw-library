import struct
import logging
from datetime import datetime as dt

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Datetime(Model):
    MODEL_ID = 0x000A
    VENDOR_ID = MODEL_ID
    DEFAULT_DATETIME_TIME = 86400 # 24 h

    # Model opcodes
    DATETIME = Model.opcode_to_bytes(0xC1, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.datetime_req_handler,
        ]
        super().__init__(gateway, handlers)

    def datetime(self, node, datetime):
        msg = bytearray()
        msg += self.DATETIME
        msg += struct.pack("<I", datetime)
        self.send(msg, node)

    def datetime_req_handler(self, event):
        if event.event_type == EventType.DATETIME_REQ:
            self.add_task(SendDatetimeTask(event.node, self))

    def datetime_send_datetime(self, node):
        self.add_task(SendDatetimeTask(node, self))


class SendDatetimeTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.DATETIME_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.retries = 0
        self.timeout = None

    def execute(self):
        now = int(dt.now().timestamp())
        self.model.datetime(self.node, now)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.debug("Sent datetime for node %s successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
