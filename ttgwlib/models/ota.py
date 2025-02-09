import struct
import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task_gw import TaskOpcode
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Ota(Model):
    MODEL_ID = 0x0012
    VENDOR_ID = MODEL_ID

    # Model opcodes
    NOTIFY_UPDATE = Model.opcode_to_bytes(0xC0, VENDOR_ID)
    STATUS = Model.opcode_to_bytes(0xC2, VENDOR_ID)
    STORE_UPDATE = Model.opcode_to_bytes(0xC4, VENDOR_ID)
    RELAY_UPDATE = Model.opcode_to_bytes(0xC6, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        self.gw = gateway
        handlers = []
        super().__init__(gateway, handlers)
        self.current_update = {}
        self.pending_nodes = []

    def clear_pending_nodes(self):
        self.pending_nodes = []

    def update_notify_send(self, node, update_type, version_major,
            version_minor, version_fix, sd_version, size):
        msg = bytearray()
        msg += self.NOTIFY_UPDATE
        msg += struct.pack("<BBBBH", update_type, version_major, version_minor,
            version_fix, sd_version)
        msg += struct.pack("<I", size)
        self.send(msg, node)

    def get_status(self, node):
        msg = bytearray()
        msg += self.STATUS
        self.send(msg, node)

    def store_update_send(self, node, size):
        msg = bytearray()
        msg += self.STORE_UPDATE
        msg += struct.pack("<I", size)
        self.send(msg, node)

    def relay_update_send(self, node):
        msg = bytearray()
        msg += self.RELAY_UPDATE
        self.send(msg, node)

    def update_notify(self, node, update_type, version_major, version_minor,
            version_fix, sd_version, size, time):
        self.add_task(OtaUpdateNotify(node, self, update_type, version_major,
            version_minor, version_fix, sd_version, size, time))

    def status(self, node):
        self.add_task(OTAStatus(node, self))

    def store_update(self, node, size, time):
        self.add_task(OtaStoreUpdate(node, self, size, time))

    def relay_update(self, node, time):
        self.add_task(OtaRelayUpdate(node, self, time))

    def update_task(self, node, time):
        """ It is used for rebooting to bootloader. """
        self.gw.models.task_gw.new_task(node, TaskOpcode.TASK_OP_UPDATE,
            time, 0, 0)


class OtaUpdateNotify(Task):
    def __init__(self, node, model, update_type, version_major, version_minor,
            version_fix, sd_version, size, time):
        super().__init__(node, [EventType.OTA_VERSION_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.update_type = update_type
        self.version_major = version_major
        self.version_minor = version_minor
        self.version_fix = version_fix
        self.sd_version = sd_version
        self.size = size
        self.time = time
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.update_notify_send(self.node, self.update_type,
            self.version_major, self.version_minor, self.version_fix,
            self.sd_version, self.size)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Node %s version rsp: %d",
            self.node.mac.hex(), event.data["status"])
        if event.data["status"] == 0:
            self.model.update_task(self.node, self.time)
            self.model.pending_nodes.append(self.node)

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class OTAStatus(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.OTA_STATUS_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.model.logger.info("Scheduled get ota status of node %s ",
                node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.get_status(self.node)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("OTA status of node %s received: %s",
            event.node.mac.hex(), event.data["status"])

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class OtaStoreUpdate(Task):
    def __init__(self, node, model, size, time):
        super().__init__(node, [EventType.OTA_STORE_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.size = size
        self.time = time
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.store_update_send(self.node, self.size)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Node %s store update rsp: %d",
            self.node.mac.hex(), event.data["status"])
        if event.data["status"] == 0:
            self.model.update_task(self.node, self.time)

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class OtaRelayUpdate(Task):
    def __init__(self, node, model, time):
        super().__init__(node, [EventType.OTA_RELAY_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.time = time
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.relay_update_send(self.node)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Node %s relay update rsp: %d",
            self.node.mac.hex(), event.data["status"])
        if event.data["status"] == 0:
            self.model.update_task(self.node, self.time)

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
