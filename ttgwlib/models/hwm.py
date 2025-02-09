import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Hwm(Model):
    MODEL_ID = 0x0016
    VENDOR_ID = MODEL_ID

    HWM_REQ = Model.opcode_to_bytes(0xC1, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.hwm_data_handler
        ]
        super().__init__(gateway, handlers)

    def hwm(self, node):
        msg = bytearray()
        msg += self.HWM_REQ
        self.send(msg, node)

    def hwm_data_handler(self, event):
        if event.event_type == EventType.HWM_DATA:
            hts = event.data["hts"]
            sht = event.data["sht"]
            fxx = event.data["fxx"]
            lps = event.data["lps"]
            self.logger.debug("[Selftest] hts: %s, sht: %s, fxx: %s, lps: %s",
                hts, sht, fxx, lps)

    def get_selftest_data(self, node):
        self.add_task(GetSelftestTask(node, self))

class GetSelftestTask(Task):
    def __init__(self, node, model):
        super().__init__(node, [EventType.HWM_ACK], [EventType.TASK_TIMEOUT])
        self.model = model
        self.model.logger.info("Scheduled get selftest of node %s ",
                node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.hwm(self.node)
        self.timeout = te.TaskTimeout(self.node, 10, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Selftest of node %s received successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
