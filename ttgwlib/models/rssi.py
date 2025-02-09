import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Rssi(Model):
    MODEL_ID = 0x000E
    VENDOR_ID = MODEL_ID

    # Model opcodes
    RSSI_NEIGHBR_REQ = Model.opcode_to_bytes(0xC1, VENDOR_ID)
    RSSI_STATUS_REQ  = Model.opcode_to_bytes(0xC3, VENDOR_ID)
    RSSI_PING_ACK = Model.opcode_to_bytes(0xC6, VENDOR_ID)
    RSSI_PING = Model.opcode_to_bytes(0xC5, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.rssi_ping_handler,
            self.rssi_ping_ack_handler,
            self.rssi_status_handler
        ]
        super().__init__(gateway, handlers)

    def rssi_neghbr_req(self, node):
        msg = bytearray()
        msg += self.RSSI_NEIGHBR_REQ
        self.send(msg, node)

    def rssi_ping_handler(self, event):
        if event.event_type == EventType.RSSI_PING:
            self.rssi_ping_ack(event.node)

    def rssi_status_handler(self, event):
        if event.event_type == EventType.RSSI_STATUS_ACK:
            self.logger.debug("RSSI status: %s", event.data["rssi"])

    def rssi_ping_ack_handler(self, event):
        if event.event_type == EventType.RSSI_PING_ACK:
            self.logger.info(f"Ping ACK from node {event.node.mac.hex()}")

    def rssi_ping(self, node):
        msg = bytearray()
        msg += self.RSSI_PING
        self.send(msg, node)

    def rssi_ping_ack(self, node):
        self.logger.debug("RSSI ping ACK")
        msg = bytearray()
        msg += self.RSSI_PING_ACK
        self.send(msg, node)

    def rssi_status_req(self, node):
        msg = bytearray()
        msg += self.RSSI_STATUS_REQ
        self.send(msg, node)

    def get_neighbr_rssi_data(self, node):
        self.add_task(GetNeighbrRssiTask(node, self))

    def get_status_rssi_data(self, node):
        self.add_task(GetStatusRssiTask(node, self))

    def ping_to_node(self, node):
        self.add_task(PingToNodeRssiTask(node, self))


class GetNeighbrRssiTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.RSSI_NEIGHBR_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.model.logger.info("Scheduled get neighbr rssi data of node %s ",
                node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.rssi_neghbr_req(self.node)
        self.timeout = te.TaskTimeout(self.node, 10, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Neighbour rssi ACK of node %s received",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class GetStatusRssiTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.RSSI_STATUS_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.model.logger.info("Scheduled get rssi status data of node %s ",
                node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.rssi_status_req(self.node)
        self.timeout = te.TaskTimeout(self.node, 10, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Rssi status of node %s received successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class PingToNodeRssiTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.RSSI_PING_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.model.logger.info("Scheduled ping to node %s ", node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.logger.info(f"Ping to node {self.node.mac.hex()}")
        self.model.rssi_ping(self.node)
        self.timeout = te.TaskTimeout(self.node, 10, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
