import struct
import logging

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class Light(Model):
    MODEL_ID = 0x0008
    VENDOR_ID = MODEL_ID

    # Model opcodes
    LIGHT = Model.opcode_to_bytes(0xC0, VENDOR_ID)
    BLINK = Model.opcode_to_bytes(0xC2, VENDOR_ID)

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = []
        super().__init__(gateway, handlers)

    def light(self, node, color):
        msg = bytearray()
        msg += self.LIGHT
        msg += struct.pack("<B", int(color[1:3], 16))
        msg += struct.pack("<B", int(color[3:5], 16))
        msg += struct.pack("<B", int(color[5:7], 16))
        self.send(msg, node)

    def blink(self, node, color, rep):
        msg = bytearray()
        msg += self.BLINK
        msg += struct.pack("<B", int(color[1:3], 16))
        msg += struct.pack("<B", int(color[3:5], 16))
        msg += struct.pack("<B", int(color[5:7], 16))
        msg += struct.pack("<H", rep)
        self.send(msg, node)

    def set_led(self, node, color):
        self.add_task(ChangeLedStateTask(node, self, color))

    def set_blink(self, node, color, rep=0):
        self.add_task(ChangeLedStateTask(node, self, color, True, rep))

    def stop_blink(self, node):
        self.add_task(ChangeLedStateTask(node, self, "#000000", True))


class ChangeLedStateTask(Task):
    def __init__(self, node, model, color, blink=False, rep=0):
        super().__init__(node, [EventType.LIGHT_ACK], [EventType.TASK_TIMEOUT])
        self.model = model
        self.color = color
        self.blink = blink
        self.rep = rep
        self.model.logger.info("Scheduled leds with color %s for node %s",
            color, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        if self.blink:
            self.model.blink(self.node, self.color, self.rep)
        else:
            self.model.light(self.node, self.color)

        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Led color of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
