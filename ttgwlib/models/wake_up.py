import logging
from datetime import datetime as dt

import ttgwlib.events.time_events as te
from ttgwlib.models.model import Model
from ttgwlib.models.task import Task
from ttgwlib.events.event import EventType

RESET_REASON = {
    0: "UNKNOWN",
    1: "RESETPIN",
    2: "DOG",
    3: "SREQ",
    4: "LOCKUP",
    5: "OFF",
    6: "LPCOMP",
    7: "DIF",
    8: "NFC",
    9: "VBUS",
    10: "MULTIPLE",
}

class WakeUp(Model):
    MODEL_ID = 0x0000
    VENDOR_ID = MODEL_ID
    DEFAULT_SLEEP_TIME = 600 # 5 min

    SLEEP = Model.opcode_to_bytes(0xC1, VENDOR_ID)
    WAIT = Model.opcode_to_bytes(0xC2, VENDOR_ID)
    ALIVE = Model.opcode_to_bytes(0xC7, VENDOR_ID)
    RESET_ACK = Model.opcode_to_bytes(0xC6, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        self.gw = gateway
        handlers = []
        super().__init__(gateway, handlers)
        self.sleep_time = self.DEFAULT_SLEEP_TIME

    @classmethod
    def get_reset_reason(cls, reset_reason):
        if reset_reason in RESET_REASON:
            return RESET_REASON[reset_reason]
        return str(reset_reason)

    def sleep(self, node, configured):
        msg = bytearray()
        msg += self.SLEEP
        msg += configured.to_bytes(1, "little")
        self.send(msg, node)

    def alive(self, node, configured):
        msg = bytearray()
        msg += self.ALIVE
        msg += configured.to_bytes(1, "little")
        self.send(msg, node)

    def wake_up(self, node):
        msg = bytearray()
        msg += self.WAIT
        self.send(msg, node)

    def wake_reset_ack(self, node):
        self.logger.debug("Wake reset ACK")
        msg = bytearray()
        msg += self.RESET_ACK
        self.send(msg, node)


class WakeTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.WAKE_ACK_WAIT],
            [EventType.WAKE_NOTIFY])
        self.model = model

    def execute(self):
        self.model.wake_up(self.node)

    def success(self, event):
        self.model.logger.info("Node %s awaked", self.node.mac.hex())

    def error(self, event):
        self.execute()


class SleepTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.WAKE_ACK_SLEEP,
            EventType.TASK_TIMEOUT], [EventType.WAKE_NOTIFY])
        self.model = model
        self.timeout = None

    def execute(self):
        self.model.sleep(self.node, True)
        self.timeout = te.TaskTimeout(self.node, 10.5, self.model.gw)

    def success(self, event):
        if self.timeout:
            self.timeout.cancel()
        event.node.sleep_timestamp = int(dt.now().timestamp())
        self.model.logger.debug("Node %s slept %d seconds",
            self.node.mac.hex(), self.model.sleep_time)

    def error(self, event):
        if self.timeout:
            self.timeout.cancel()
        self.execute()


class AliveTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.WAKE_ACK_ALIVE,
            EventType.TASK_TIMEOUT], [EventType.WAKE_NOTIFY])
        self.model = model
        self.timeout = None

    def execute(self):
        self.model.alive(self.node, True)
        self.timeout = te.TaskTimeout(self.node, 10.5, self.model.gw)

    def success(self, event):
        if self.timeout:
            self.timeout.cancel()
        #FIXME: sqlite on merge
        self.model.logger.debug("Node %s alive", self.node.mac.hex())

    def error(self, event):
        if self.timeout:
            self.timeout.cancel()
        self.execute()
