import struct
import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Power(Model):
    MODEL_ID = 0x0014
    VENDOR_ID = MODEL_ID

    POWER = Model.opcode_to_bytes(0xC0, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.power_ack_handler,
        ]
        super().__init__(gateway, handlers)

    def power(self, node, radio_power, dcdc_mode):
        msg = bytearray()
        msg += self.POWER
        msg += struct.pack("<B", radio_power)
        msg += struct.pack("<B", dcdc_mode)
        self.send(msg, node)

    def power_ack_handler(self, event):
        if event.event_type == EventType.POWER_ACK:
            self.logger.debug("Ack power conf received.")

    def set_power(self, node, radio_power, dcdc_mode):
        self.add_task(ChangePowerTask(node, self, radio_power, dcdc_mode))


class ChangePowerTask(Task):
    def __init__(self, node, model, radio_power, dcdc_mode):
        super().__init__(node, [EventType.POWER_ACK], [EventType.TASK_TIMEOUT])
        self.model = model
        self.radio_power = radio_power
        self.dcdc_mode = dcdc_mode
        self.model.logger.info("Scheduled setting power (radio_power: %s, "
            + "dcdc_mode: %s) for node %s", radio_power, dcdc_mode,
            node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.power(self.node, self.radio_power, self.dcdc_mode)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Power config of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
