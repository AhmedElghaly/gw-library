import struct
import logging
from datetime import datetime as dt

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.models.task_gw import TaskOpcode
from ttgwlib.events.event import EventType

SHT4X_CONF = {
    0: "SHT4X_REP_HIGH",
    1: "SHT4X_REP_MED",
    2: "SHT4X_REP_LOW",
    3: "SHT4X_REP_HEAT_H_1S",
    4: "SHT4X_REP_HEAT_H_0_1S",
    5: "SHT4X_REP_HEAT_M_1S",
    6: "SHT4X_REP_HEAT_M_0_1S",
    7: "SHT4X_REP_HEAT_L_1S",
    8: "SHT4X_REP_HEAT_L_0_1S"
}

class NrfTemp(Model):
    MODEL_ID = 0x0002
    VENDOR_ID = MODEL_ID
    DEFAULT_NRFTEMP_PERIOD = 600 # 10 min
    DEFAULT_NRFTEMP_IAQ_PERIOD = 300 # 5 min
    DEFAULT_NRFTEMP_CO2_PERIOD = 300 # 5 min

    IA = Model.opcode_to_bytes(0xC2, VENDOR_ID)
    TEMP_DATA_ACK = Model.opcode_to_bytes(0xC5, VENDOR_ID)
    TEMP_CONFIG = Model.opcode_to_bytes(0xC7, VENDOR_ID)
    TEMP_CALIBRATE = Model.opcode_to_bytes(0xC9, VENDOR_ID)
    TEMP_CAL_RESET = Model.opcode_to_bytes(0xCB, VENDOR_ID)

    def __init__(self, gateway):
        self.gw = gateway
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.temp_data_handler,
            self.iaq_data_handler,
            self.co2_data_handler,
        ]
        super().__init__(gateway, handlers)

    def ia(self, node, status, n):
        msg = bytearray()
        msg += self.IA
        msg += struct.pack("<B", status)
        msg += struct.pack("<B", n)
        self.send(msg, node)

    @classmethod
    def get_config_modes(cls):
        return SHT4X_CONF

    def config(self, node, mode):
        msg = bytearray()
        msg += self.TEMP_CONFIG
        msg += struct.pack("<B", mode)
        self.send(msg, node)

    def calibrate(self, node, temp_offset, humd_offset, press_offset):
        msg = bytearray()
        msg += self.TEMP_CALIBRATE
        msg += struct.pack("<h", int(temp_offset * 100))
        msg += struct.pack("<b", humd_offset)
        msg += struct.pack("<B", (press_offset) & 0xFF)
        msg += struct.pack("<B", (press_offset >> 8) & 0xFF)
        msg += struct.pack("<B", (press_offset >> 16) & 0xFF)
        self.send(msg, node)

    def calib_reset(self, node, temp, humd, press):
        msg = bytearray()
        msg += self.TEMP_CAL_RESET
        msg += struct.pack("<h", temp)
        msg += struct.pack("<b", humd)
        msg += struct.pack("<B", (press) & 0xFF)
        msg += struct.pack("<B", (press >> 8) & 0xFF)
        msg += struct.pack("<B", (press >> 16) & 0xFF)
        self.send(msg, node)

    def temp_data_ack(self, node):
        self.logger.debug("nrftemp ACK")
        msg = bytearray()
        msg += self.TEMP_DATA_ACK
        self.send(msg, node)

    def temp_data_handler(self, event):
        if event.event_type in (EventType.TEMP_DATA,
                EventType.TEMP_DATA_RELIABLE):
            if event.event_type == EventType.TEMP_DATA_RELIABLE:
                self.temp_data_ack(event.node)
            self.logger.debug("Temp received: %d, %s, %d, %d, %d, %d, %d",
                event.data["src"], event.node.mac.hex(), event.data["temp"],
                event.data["hum"], event.data["press"], event.data["rssi"],
                event.data["ttl"])
            event.node.msg_timestamp = int(dt.now().timestamp())

    def iaq_data_handler(self, event):
        if event.event_type == EventType.IAQ_DATA:
            self.logger.debug("Iaq received: %d, %s, %d, %d, %d %d",
                event.data["src"], event.node.mac.hex(), event.data["iaq"],
                event.data["tvoc"], event.data["etoh"], event.data["eco2"])

    def co2_data_handler(self, event):
        if event.event_type == EventType.CO2_DATA:
            self.logger.debug("CO2 received: %d, %s, %d ppm (cal_status: %d,"
                + " abc_time: %d)", event.data["src"], event.node.mac.hex(),
                event.data["co2"], event.data["cal_status"],
                event.data["abc_time"])

    def set_nrftemp_rate(self, node, rate):
        self.gw.models.task_gw.set_rate(node, TaskOpcode.TASK_OP_NRFTEMP, rate)

    def set_nrftemp_rate_legacy(self, node, rate):
        self.gw.models.task_gw.set_rate_legacy(node, TaskOpcode.TASK_OP_NRFTEMP,
            rate)

    def set_iaq_rate(self, node, rate):
        self.gw.models.task_gw.set_rate(node,
            TaskOpcode.TASK_OP_NRFTEMP_READ_IAQ, rate)

    def set_iaq_rate_legacy(self, node, rate):
        self.gw.models.task_gw.set_rate_legacy(node,
            TaskOpcode.TASK_OP_NRFTEMP_READ_IAQ, rate)

    def set_co2_rate(self, node, rate):
        self.gw.models.task_gw.set_rate(node, TaskOpcode.TASK_OP_NRFTEMP_CO2,
            rate)

    def set_co2_rate_legacy(self, node, rate):
        self.gw.models.task_gw.set_rate_legacy(node,
            TaskOpcode.TASK_OP_NRFTEMP_CO2, rate)

    def set_ia(self, node, status, n):
        self.add_task(ChangeIaTask(node, self, status, n))

    def set_configuration(self, node, mode):
        self.add_task(ChangeConfigTask(node, self, mode))

    def set_calibration(self, node, temp_offset, humd_offset, press_offset):
        self.add_task(ChangeCalibrationTask(node, self,  temp_offset,
                humd_offset, press_offset))

    def reset_calibration(self, node, temp, humd, press):
        self.add_task(ResetCalibrationTask(node, self,  temp, humd, press))


class ChangeIaTask(Task):
    def __init__(self, node, model, status, n):
        super().__init__(node, [EventType.IA_ACK], [EventType.TASK_TIMEOUT])
        self.model = model
        self.status = status
        self.n = n
        self.model.logger.info("Scheduled setting ia config (status: %s, n: %s)"
            + " for node %s", status, n, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.ia(self.node, self.status, self.n)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("IA config of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class ChangeConfigTask(Task):
    def __init__(self, node, model, mode):
        super().__init__(node, [EventType.TEMP_CONFIG_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.mode = mode
        self.model.logger.info("Scheduled setting node configuration (mode: %s)"
            + " for node %s", SHT4X_CONF[mode], node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.config(self.node, self.mode)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Sensor config of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class ChangeCalibrationTask(Task):
    def __init__(self, node, model, temp_offset, humd_offset, press_offset):
        super().__init__(node, [EventType.TEMP_CALIB_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.temp_offset = temp_offset
        self.humd_offset = humd_offset
        self.press_offset = press_offset
        self.model.logger.info("Scheduled setting node calibration"
            + " (Temp offset: %.2f, Humd offset: %d, Press offset: %d)"
            + " for node %s", temp_offset, humd_offset, press_offset,
            node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.calibrate(self.node, self.temp_offset, self.humd_offset,
                self.press_offset)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Calibration of node %s changed successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class ResetCalibrationTask(Task):
    def __init__(self, node, model, temp, humd, press):
        super().__init__(node, [EventType.TEMP_CALIB_RESET_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.temp = temp
        self.humd = humd
        self.press = press
        self.model.logger.info("Scheduled resetting node calibration"
            + f" (Temp: {temp}, Humd: {humd}, Press: {press})"
            + " for node %s", node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.calib_reset(self.node, self.temp, self.humd, self.press)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Calibration of node %s reset successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
