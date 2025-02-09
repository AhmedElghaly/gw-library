import struct
import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Tap(Model):
    MODEL_ID = 0x0006
    VENDOR_ID = MODEL_ID

    STATE = Model.opcode_to_bytes(0xC1, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = []
        super().__init__(gateway, handlers)

    def state(self, node, state):
        msg = bytearray()
        msg += self.STATE
        msg += struct.pack("<B", state)
        self.send(msg, node)

    def set_accel_state(self, node, state):
        self.add_task(ChangeAccelTask(node, self, state))


class ChangeAccelTask(Task):
    def __init__(self, node, model, state):
        super().__init__(node, [EventType.TAP_ACK_CONF],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.state = state
        self.model.logger.info("Scheduled changing accel state of node %s "
            + "to %d", node.mac.hex(), state)
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.state(self.node, self.state)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Accel state of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
