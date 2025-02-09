import struct
import logging
from datetime import datetime as dt

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.models.task_gw import TaskOpcode
from ttgwlib.events.event import EventType


class Pwmt(Model):
    MODEL_ID = 0x001C
    VENDOR_ID = MODEL_ID
    DEFAULT_PWMT_PERIOD = 30  # 30 sec

    CONF = Model.opcode_to_bytes(0xC1, VENDOR_ID)
    CONV = Model.opcode_to_bytes(0xC3, VENDOR_ID)

    def __init__(self, gateway):
        self.gw = gateway
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.pwmt_data_handler,
        ]
        super().__init__(gateway, handlers)

    def conf(self, node, phases, stats, values_ph, values_tot):
        c1 = (phases & 0b1111) | (stats & 0b111) << 4
        c2 = (values_ph & 0b1111) | (values_tot & 0b1111) << 4

        msg = bytearray()
        msg += self.CONF
        msg += struct.pack("<B", c1)
        msg += struct.pack("<B", c2)
        self.send(msg, node)

    def conv(self, node, kv, ki):
        k = (ki & 0xFFFFFFF) | ((kv & 0xFFFFFFF) << 28)
        msg = bytearray()
        msg += self.CONV
        msg += k.to_bytes(7, byteorder="little")
        self.send(msg, node)

    def pwmt_data_handler(self, event):
        if event.event_type == EventType.PWMT_DATA:
            phase_id = event.data["ctl"] & 0b11
            message_id = (event.data["ctl"] >> 2) & 0b11
            value_type = (event.data["ctl"] >> 4) & 0b11
            calc_status = (event.data["ctl"] >> 6) & 0b11

            if calc_status == 1: # Invalid data
                self.logger.debug("Pwmt: INVALID_DATA (L%d)", phase_id)
                return

            value_type_str = ""
            if value_type == 0b00:
                value_type_str = "avg"
            elif value_type == 0b01:
                value_type_str = "max"
            elif value_type == 0b10:
                value_type_str = "min"

            # TODO: Remove pwmt logs since they take up too much storage space
            if phase_id == 0:
                if message_id == 0:
                    self.logger.debug("Pwmt: %d, %s, [TO][%s] status:%d, " +
                        "P:%.2fW, Q:%.2fVAr, S:%.2fVA (%d dBm)",
                        event.data["src"], event.node.mac.hex(), value_type_str,
                        calc_status, event.data["p_tot"], event.data["q_tot"],
                        event.data["s_tot"], event.data["rssi"])
                elif message_id == 1:
                    self.logger.debug("Pwmt: %d, %s, [TO][%s] status:%d, " +
                        "PH12:%.2fdeg, PH23:%.2fdeg, PH31:%.2fdeg (%d dBm)",
                        event.data["src"], event.node.mac.hex(), value_type_str,
                        calc_status, event.data["ph12"], event.data["ph23"],
                        event.data["ph31"], event.data["rssi"])
                elif message_id == 2:
                    self.logger.debug("Pwmt: %d, %s, [TO][%s] status:%d, " +
                        "V12:%.2fV, V23:%.2fV, V31:%.2fV (%d dBm)",
                        event.data["src"], event.node.mac.hex(), value_type_str,
                        calc_status, event.data["v12"], event.data["v23"],
                        event.data["v31"], event.data["rssi"])
                elif message_id == 3:
                    self.logger.debug("Pwmt: %d, %s, [TO][%s] status:%d, " +
                        "E:%dWh (%d dBm)",
                        event.data["src"], event.node.mac.hex(), value_type_str,
                        calc_status, event.data["e_tot"], event.data["rssi"])
            else:
                if message_id == 0:
                    self.logger.debug("Pwmt: %d, %s, [L%d][%s] status:%d, " +
                        "V:%.2fV, I:%.2fA, f:%.2fHz (%d dBm)",
                        event.data["src"], event.node.mac.hex(), phase_id,
                        value_type_str, calc_status, event.data["v"],
                        event.data["i"], event.data["f"], event.data["rssi"])
                elif message_id == 1:
                    self.logger.debug("Pwmt: %d, %s, [L%d][%s] status:%d, " +
                        "P:%.2fW, pf:%.2f(%s) (%d dBm)",
                        event.data["src"], event.node.mac.hex(), phase_id,
                        value_type_str, calc_status, event.data["p"],
                        event.data["pf"], "ind" if event.data["ind"] else "cap",
                        event.data["rssi"])
                elif message_id == 2:
                    self.logger.debug("Pwmt: %d, %s, [L%d][%s] status:%d, " +
                        "Q:%.2fVAr, S:%.2fVA, ph:%.2fdeg (%d dBm)",
                        event.data["src"], event.node.mac.hex(), phase_id,
                        value_type_str, calc_status, event.data["q"],
                        event.data["s"], event.data["ph"], event.data["rssi"])
                elif message_id == 3:
                    self.logger.debug("Pwmt: %d, %s, [L%d][%s] status:%d, " +
                        "E:%dWh (%d dBm)",
                        event.data["src"], event.node.mac.hex(), phase_id,
                        value_type_str, calc_status, event.data["e"],
                        event.data["rssi"])
            event.node.msg_timestamp = int(dt.now().timestamp())

    def set_pwmt_rate(self, node, rate):
        self.gw.models.task_gw.set_rate(node, TaskOpcode.TASK_OP_PWMT_READ,
            rate)

    def set_pwmt_rate_legacy(self, node, rate):
        self.gw.models.task_gw.set_rate_legacy(node,
            TaskOpcode.TASK_OP_PWMT_READ, rate)

    def set_pwmt_conf(self, node, phases, stats, values_ph, values_tot):
        self.add_task(ConfigPwmtTask(node, self, phases, stats, values_ph,
                values_tot))

    def set_pwmt_conv(self, node, kv, ki):
        self.add_task(ConversionPwmtTask(node, self, kv, ki))

class ConfigPwmtTask(Task):
    def __init__(self, node, model, phases, stats, values_ph, values_tot):
        super().__init__(node, [EventType.PWMT_CONFIG_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.phases = phases
        self.stats = stats
        self.values_ph = values_ph
        self.values_tot = values_tot
        self.model.logger.info("Scheduled setting pwmt config "
            + "(phases %s, stats %s, values_ph %s, values_tot %s, "
            + " for node %s", phases, stats, values_ph,
            values_tot, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.conf(self.node, self.phases, self.stats, self.values_ph,
            self.values_tot)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.timer.cancel()
        self.model.logger.info("Power meter config of node %s "
            + "changed successfully", event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)

class ConversionPwmtTask(Task):
    def __init__(self, node, model, kv, ki):
        super().__init__(node, [EventType.PWMT_CONV_ACK],
                [EventType.TASK_TIMEOUT])
        self.model = model
        self.kv = kv
        self.ki = ki
        mac = node.mac.hex()
        self.model.logger.info("Scheduled setting pwmt conversion factor "
            + "(kv %.3f, ki %.3f) for node %s", kv/1000, ki/1000, mac)
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.conv(self.node, self.kv, self.ki)
        self.timeout = te.TaskTimeout(self.node, 2.5, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.timer.cancel()
        self.model.logger.info("Power meter conversion factor of node %s "
            + "changed successfully", event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
