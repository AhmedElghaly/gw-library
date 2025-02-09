import struct
import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Output(Model):
    MODEL_ID = 0x001E
    VENDOR_ID = MODEL_ID

    DAC = Model.opcode_to_bytes(0xC0, VENDOR_ID)
    DIG = Model.opcode_to_bytes(0xC2, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.output_dac_ack_handler,
            self.output_dig_ack_handler,
        ]
        super().__init__(gateway, handlers)

    def output_dac(self, node, dac_value):
        msg = bytearray()
        msg += self.DAC
        msg += struct.pack("<f", dac_value)
        self.send(msg, node)

    def output_dac_ack_handler(self, event):
        if event.event_type == EventType.OUTPUT_DAC_ACK:
            self.logger.debug("Ack DAC output received.")

    def output_dig(self, node, dig_status):
        msg = bytearray()
        msg += self.DIG
        msg += struct.pack("<B", dig_status)
        self.send(msg, node)

    def output_dig_ack_handler(self, event):
        if event.event_type == EventType.OUTPUT_DIG_ACK:
            self.logger.debug("Ack digital output received.")

    def set_dac(self, node, dac_value):
        self.add_task(ChangeDacOutput(node, self, dac_value))

    def set_digital(self, node, dig_status):
        self.add_task(ChangeDigOutput(node, self, dig_status))


class ChangeDacOutput(Task):
    def __init__(self, node, model, dac_value):
        super().__init__(node, [EventType.OUTPUT_DAC_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.dac_value = dac_value
        self.model.logger.info("Scheduled setting dac (dac_value: %f)"
            + " for node %s", dac_value, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.output_dac(self.node, self.dac_value)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("dac value of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class ChangeDigOutput(Task):
    def __init__(self, node, model, dig_status):
        super().__init__(node, [EventType.OUTPUT_DIG_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.dig_status = dig_status
        self.model.logger.info("Scheduled setting dig output (dig_status: %d)"
            + " for node %s", dig_status, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.output_dig(self.node, self.dig_status)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("digital value of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
