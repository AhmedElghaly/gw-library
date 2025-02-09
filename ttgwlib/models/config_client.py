import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class ConfigurationClient(Model):
    VENDOR_ID = None
    MODEL_ID = 0x0000

    NODE_RESET = Model.opcode_to_bytes(0x8049)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        super().__init__(gateway, [])

    def reset(self, node):
        message = self.NODE_RESET
        self.send(message, node)

    def reset_node(self, node):
        self.add_task(ResetTask(node, self))


class ResetTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.NODE_RESET, EventType.TASK_TIMEOUT],
            [EventType.WAKE_NOTIFY])
        self.model = model
        self.timeout = None
        self.model.logger.info("Scheduled reset node %s", node.mac.hex())

    def execute(self):
        self.model.logger.debug("Resetting node %s", self.node)
        self.model.reset(self.node)
        self.timeout = te.TaskTimeout(self.node, 10.5, self.model.gw)

    def success(self, event):
        if self.timeout:
            self.timeout.cancel()
        self.model.logger.info("Node %s reset and removed from database",
            event.node.mac.hex())
        self.model.gw.replay_cache.remove_node(event.node.unicast_addr)
        self.model.gw.node_db.remove_node(event.node)

    def error(self, event):
        if self.timeout:
            self.timeout.cancel()
        self.execute()
