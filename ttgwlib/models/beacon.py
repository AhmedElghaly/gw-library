import struct
import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Beacon(Model):
    MODEL_ID = 0x0018
    VENDOR_ID = MODEL_ID

    START_BEACON = Model.opcode_to_bytes(0xC0, VENDOR_ID)
    STOP_BEACON = Model.opcode_to_bytes(0xC2, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.beacon_ack_handler,
        ]
        self.bcn_tid = 0
        super().__init__(gateway, handlers)

    def start_beacon_send(self, node, period_ms, tid):
        msg = bytearray()
        msg += self.START_BEACON
        msg += struct.pack("<H", period_ms)
        msg += struct.pack("<B", tid)
        self.send(msg, node)

    def stop_beacon_send(self, node, tid):
        msg = bytearray()
        msg += self.STOP_BEACON
        msg += struct.pack("<B", tid)
        self.send(msg, node)

    def beacon_ack_handler(self, event):
        if event.event_type == EventType.BEACON_START_ACK:
            tid = event.data["tid"]
            self.logger.debug("Ack Beacon Start received. Tid: %d", tid)
        elif event.event_type == EventType.BEACON_STOP_ACK:
            tid = event.data["tid"]
            self.logger.debug("Ack Beacon Stop received. Tid: %d", tid)

    def start_beacon(self, node, period_ms):
        self.add_task(StartBeaconTask(node, self, period_ms, self.bcn_tid))
        self.bcn_tid = (self.bcn_tid + 1) if (self.bcn_tid < 100) else 0

    def stop_beacon(self, node):
        self.add_task(StopBeaconTask(node, self, self.bcn_tid))
        self.bcn_tid = (self.bcn_tid + 1) if (self.bcn_tid < 100) else 0


class StartBeaconTask(Task):
    def __init__(self, node, model, period_ms, tid):
        super().__init__(node, [EventType.BEACON_START_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.period_ms = period_ms
        self.tid = tid
        self.model.logger.info("Scheduled setting beacon (period: %d ms) for"
            + " node %s", period_ms, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.start_beacon_send(self.node, self.period_ms, self.tid)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Beacon config for node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class StopBeaconTask(Task):
    def __init__(self, node, model, tid):
        super().__init__(node, [EventType.BEACON_STOP_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.tid = tid
        self.model.logger.info("Scheduled stopping beacon for node %s",
            node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.stop_beacon_send(self.node, self.tid)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Beacon stopped for node %s successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
