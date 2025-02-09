import struct
import logging
from datetime import datetime as dt

import ttgwlib.events.time_events as te
from ttgwlib.models.task import Task
from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType


class TaskOpcode:
    """ List of Task Opcodes """
    TASK_OP_CONF = 0x01         # Opcode for starting configuration FSM
    TASK_OP_NRFTEMP = 0x02      # Opcode for starting unreliable nrftemp FSM
    TASK_OP_BAT = 0x03          # Opcode for starting battery FSM
    TASK_OP_SET_BLUE_LED = 0x04 # Opcode for toggling the blue led
    TASK_OP_REQ_DATETIME = 0x05 # Opcode for the node to request datetime
    TASK_OP_UPDATE = 0x07       # Opcode for ota update
    TASK_OP_SEND_NODES = 0x08   # Opcode for sending msg to other nodes
    TASK_OP_REBOOT = 0x09       # Opcode for rebooting
    TASK_OP_NRFTEMP_START_IAQ = 0x0A # Opcode for starting iaq FSM
    TASK_OP_NRFTEMP_READ_IAQ = 0x0B  # Opcode for start reading in iaq FSM
    TASK_OP_NRFTEMP_STOP_IAQ = 0x0C  # Opcode for stop reading in iaq FSM
    TASK_OP_NRFTEMP_CO2 = 0x0D       # Opcode for starting co2 FSM
    TASK_OP_NRFTEMP_START_CO2 = 0x0E # Opcode for starting co2 measurement
    TASK_OP_NRFTEMP_STOP_CO2 = 0x0F  # Opcode for stoping co2 measurement
    TASK_OP_NRFTEMP_RELIABLE = 0x10  # Opcode for starting reliable nrftemp FSM
    TASK_OP_LEDS_DISP_TEMP = 0x12    # Opcode for show the temperature with led
    TASK_OP_LEDS_DISP_HUMD = 0x13    # Opcode for show the humidity with led
    TASK_OP_LEDS_DISP_PRESS = 0x14   # Opcode for show the pressure with led
    TASK_OP_LEDS_DISP_CO2 = 0x15     # Opcode for show the co2 with led
    TASK_OP_LEDS_DISP_IAQ = 0x16     # Opcode for show the iaq with led
    TASK_OP_LEDS_DISP_BAT = 0x18     # Opcode for show the battery with led
    TASK_OP_LEDS_DISP_RSSI = 0x19    # Opcode for show the rssi with led
    TASK_OP_CO2_ZERO_CALIB = 0x1B    # Opcode for perform zero calibration
    TASK_OP_CO2_TARGET_CALIB = 0x1C  # Opcode for perform CO2 400ppm calibration
    TASK_OP_PWMT_READ = 0x1D         # Opcode for power meter measurement
    TASK_OP_PWMT_START = 0x1E        # Opcode for start power meter sampling
    TASK_OP_PWMT_STOP = 0x1F         # Opcode for stop power meter sampling
    TASK_OP_BLINK_START = 0x20       # Opcode for start led blink
    TASK_OP_BLINK_STOP = 0x21        # Opcode for stop led blink

    @classmethod
    def op_to_string(cls, op):
        for attr in dir(cls):
            if getattr(cls, attr) == op:
                return attr[8:]
        return "UNKNONW_TASK"

class TaskGw(Model):
    MODEL_ID = 0x000C
    VENDOR_ID = MODEL_ID

    # Task type
    CLOCK_MONO = 0
    CLOCK_REAL = 1

    # Model opcodes
    CONF_REAL = Model.opcode_to_bytes(0xC9, VENDOR_ID)
    CONF_MONO = Model.opcode_to_bytes(0xCA, VENDOR_ID)
    DEL =  Model.opcode_to_bytes(0xC2, VENDOR_ID)
    DEL_OP = Model.opcode_to_bytes(0xC4, VENDOR_ID)
    GET = Model.opcode_to_bytes(0xC6, VENDOR_ID)
    CHANGE_REAL = Model.opcode_to_bytes(0xCB, VENDOR_ID)
    CHANGE_MONO = Model.opcode_to_bytes(0xCC, VENDOR_ID)

    TASK_ERRORS = {
        0:  "TASK_SUCCESS",
        -1: "TASK_ERR_INVALID_OP",
        -2: "TASK_ERR_ARRAY_FULL",
        -3: "TASK_ERR_ALRDY_SCHD",
        -4: "TASK_ERR_INVALID_ID",
        -5: "TASK_ERR_NOT_CONFIG"
    }

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.task_ack_handler,
        ]
        self.task_tid = 0
        self.node_tasks = {}
        super().__init__(gateway, handlers)

    def task_gw_conf_mono(self, node, opcode, event_date, period):
        msg = bytearray()
        msg += self.CONF_MONO
        msg += struct.pack("<B", opcode)
        msg += struct.pack("<I", event_date)
        msg += bytes([period & 0xFF, period>>8 & 0xFF, period>>16 & 0xFF])
        self.send(msg, node)

    def task_gw_conf_real(self, node, opcode, event_date, period):
        msg = bytearray()
        msg += self.CONF_REAL
        msg += struct.pack("<B", opcode)
        msg += struct.pack("<I", event_date)
        msg += bytes([period & 0xFF, period>>8 & 0xFF, period>>16 & 0xFF])
        self.send(msg, node)

    def task_gw_change_mono(self, node, opcode, event_date, period):
        msg = bytearray()
        msg += self.CHANGE_MONO
        msg += struct.pack("<B", opcode)
        msg += struct.pack("<I", event_date)
        msg += bytes([period & 0xFF, period>>8 & 0xFF, period>>16 & 0xFF])
        self.send(msg, node)

    def task_gw_change_real(self, node, opcode, event_date, period):
        msg = bytearray()
        msg += self.CHANGE_REAL
        msg += struct.pack("<B", opcode)
        msg += struct.pack("<I", event_date)
        msg += bytes([period & 0xFF, period>>8 & 0xFF, period>>16 & 0xFF])
        self.send(msg, node)

    def task_gw_delete(self, node, index, tid):
        msg = bytearray()
        msg += self.DEL
        msg += struct.pack("<B", index)
        msg += struct.pack("<B", tid)
        self.send(msg, node)

    def task_gw_delete_op(self, node, opcode, tid):
        msg = bytearray()
        msg += self.DEL_OP
        msg += struct.pack("<B", opcode)
        msg += struct.pack("<B", tid)
        self.send(msg, node)

    def task_gw_get_tasks(self, node):
        msg = bytearray()
        msg += self.GET
        self.send(msg, node)

    def task_ack_handler(self, event):
        if event.event_type == EventType.TASK_ACK:
            task_index = event.data["task_index"]
            tid = event.data["tid"]
            if task_index >= 0:
                self.logger.debug("Ack task conf received. Tid: %d. Index: %d",
                    tid, task_index)
            else:
                self.logger.debug("Ack task conf received. Tid: %d. Error: %s",
                    tid, self.TASK_ERRORS[task_index])

        elif event.event_type == EventType.TASK_DELETE_ACK:
            delete_code = event.data["delete_code"]
            tid = event.data["tid"]
            self.logger.debug("Ack task delete received. Tid: %d. Code: %s",
                tid, self.TASK_ERRORS[delete_code])

        elif event.event_type == EventType.TASK_DELETE_OP_ACK:
            delete_code = event.data["delete_code"]
            tid = event.data["tid"]
            self.logger.debug("Ack task delete op received. Tid: %d. Code: %s",
                tid, self.TASK_ERRORS[delete_code])

        elif event.event_type == EventType.TASK_SEND_TASKS:
            opcode = event.data["opcode"]
            event_date = event.data["event_date"]
            period = event.data["period"]
            self.logger.debug("Tasks received. op: %d (%s), event date: %d, " +
                "period: %d", opcode, TaskOpcode.op_to_string(opcode),
                event_date, period)

        elif event.event_type == EventType.WAKE_RESET:
            mac = event.node.mac.hex()
            if mac not in self.node_tasks:
                self.node_tasks[mac] = {"configured_tasks": []}

    def new_task(self, node, opcode, event_date, period, task_type):
        self.add_task(NewTaskGwTask(node, self, opcode, event_date, period,
            task_type))

    def change_task(self, node, opcode, event_date, period, task_type):
        self.add_task(ChangeTaskGwTask(node, self, opcode, event_date, period,
            task_type))

    def delete_task(self, node, index):
        self.add_task(DeleteTaskGwTask(node, self, index, self.task_tid))
        self.task_tid = (self.task_tid + 1) if (self.task_tid < 100) else 0

    def delete_task_op(self, node, opcode):
        self.add_task(DeleteTaskOpGwTask(node, self, opcode, self.task_tid))
        self.task_tid = (self.task_tid + 1) if (self.task_tid < 100) else 0

    def get_tasks(self, node):
        self.add_task(GetTasksGwTask(node, self))

    def set_rate(self, node, opcode, rate):
        now = int(dt.now().timestamp())
        self.change_task(node, opcode, now, rate, 0)

    def set_rate_legacy(self, node, opcode, rate):
        self.delete_task_op(node, opcode)
        now = int(dt.now().timestamp())
        self.new_task(node, opcode, now, rate, 0)

    def set_sleep_time(self, node):
        sleep_time = self.gw.models.wake_up.sleep_time
        first_awake = int(dt.now().timestamp()) + sleep_time
        self.change_task(node, TaskOpcode.TASK_OP_CONF, first_awake,
            sleep_time, 0)

    def set_sleep_time_legacy(self, node, *, first_time=False):
        if not first_time:
            self.delete_task_op(node, TaskOpcode.TASK_OP_CONF)
        sleep_time = self.gw.models.wake_up.sleep_time
        first_awake = int(dt.now().timestamp()) + sleep_time
        self.new_task(node, TaskOpcode.TASK_OP_CONF, first_awake, sleep_time, 0)

    def get_configured_tasks(self, node):
        mac = node.mac.hex()
        if mac not in self.node_tasks:
            return None
        return self.node_tasks[mac]


class TaskGwBase(Task):
    opcode = -1
    def __str__(self):
        return (self.__class__.__name__[:-4] + "-"
            + TaskOpcode.op_to_string(self.opcode))

    def execute(self):
        raise NotImplementedError

    def success(self, event):
        raise NotImplementedError

    def error(self, event):
        raise NotImplementedError


class NewTaskGwTask(TaskGwBase):
    def __init__(self, node, model, opcode, event_date, period, task_type):
        super().__init__(node, [EventType.TASK_ACK], [EventType.TASK_TIMEOUT])
        self.model = model
        self.opcode = opcode
        self.event_date = event_date
        self.period = period
        self.task_type = task_type
        self.model.logger.info("Scheduled task %s (%d) for node %s",
            TaskOpcode.op_to_string(opcode), opcode, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        if self.task_type == self.model.CLOCK_MONO:
            self.model.task_gw_conf_mono(self.node, self.opcode,
                    self.event_date, self.period)
        else:
            self.model.task_gw_conf_real(self.node, self.opcode,
                    self.event_date, self.period)
        self.timeout = te.TaskTimeout(self.node, 6, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        mac = event.node.mac.hex()
        op = TaskOpcode.op_to_string(self.opcode)
        if self.opcode == TaskOpcode.TASK_OP_CONF:
            event.node.sleep_period = self.period
            self.model.gw.node_db.store_node(event.node)
        self.model.logger.info("Task %s (%d) ACK for node %s received",
            TaskOpcode.op_to_string(self.opcode), self.opcode, mac)
        if mac not in self.model.node_tasks:
            self.model.node_tasks[mac] = {"configured_tasks": []}
        if ((event.data["task_index"] >= 0 or event.data["task_index"] == -3)
                and op not in self.model.node_tasks[mac]["configured_tasks"]
                and self.period != 0):
            self.model.node_tasks[mac]["configured_tasks"].append(op)
    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class ChangeTaskGwTask(TaskGwBase):
    def __init__(self, node, model, opcode, event_date, period, task_type):
        super().__init__(node, [EventType.TASK_CHANGE_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.opcode = opcode
        self.event_date = event_date
        self.period = period
        self.task_type = task_type
        self.model.logger.info("Scheduled changing task %s (%d) for node %s",
            TaskOpcode.op_to_string(opcode), opcode, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        if self.task_type == self.model.CLOCK_MONO:
            self.model.task_gw_change_mono(self.node, self.opcode,
                    self.event_date, self.period)
        else:
            self.model.task_gw_change_real(self.node, self.opcode,
                    self.event_date, self.period)
        self.timeout = te.TaskTimeout(self.node, 6, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        mac = event.node.mac.hex()
        op = TaskOpcode.op_to_string(self.opcode)
        if self.opcode == TaskOpcode.TASK_OP_CONF:
            event.node.sleep_period = self.period
            self.model.gw.node_db.store_node(event.node)
        self.model.logger.info("Task %s (%d) change ACK for node %s received",
            TaskOpcode.op_to_string(self.opcode), self.opcode, mac)
        if mac not in self.model.node_tasks:
            self.model.node_tasks[mac] = {"configured_tasks": []}
        if ((event.data["task_index"] >= 0 or event.data["task_index"] == -3)
                and op not in self.model.node_tasks[mac]["configured_tasks"]
                and self.period != 0):
            self.model.node_tasks[mac]["configured_tasks"].append(op)

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class DeleteTaskGwTask(TaskGwBase):
    def __init__(self, node, model, index, tid):
        super().__init__(node, [EventType.TASK_DELETE_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.index = index
        self.tid = tid
        self.model.logger.info("Scheduled deleting task with index %d for"
            + " node %s", index, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.task_gw_delete(self.node, self.index, self.tid)
        self.timeout = te.TaskTimeout(self.node, 6, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Delete task ACK for node %s received",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class DeleteTaskOpGwTask(TaskGwBase):
    def __init__(self, node, model, opcode, tid):
        super().__init__(node, [EventType.TASK_DELETE_OP_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.opcode = opcode
        self.tid = tid
        self.model.logger.info("Scheduled deleting task %s (%d) for node %s",
            TaskOpcode.op_to_string(opcode), opcode, node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.task_gw_delete_op(self.node, self.opcode, self.tid)
        self.timeout = te.TaskTimeout(self.node, 6, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        mac = event.node.mac.hex()
        self.model.logger.info("Delete task ACK for node %s received", mac)
        if mac not in self.model.node_tasks:
            self.model.node_tasks[mac] = {"configured_tasks": []}
        op = TaskOpcode.op_to_string(self.opcode)
        if op in self.model.node_tasks[mac]["configured_tasks"]:
            self.model.node_tasks[mac]["configured_tasks"].remove(op)

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)


class GetTasksGwTask(TaskGwBase):
    def __init__(self, node, model):
        super().__init__(node, [EventType.TASK_GET_TASKS_ACK],
            [EventType.TASK_TIMEOUT])
        self.model = model
        self.model.logger.info("Scheduled getting tasks for node %s",
            node.mac.hex())
        self.retries = 0
        self.timeout = None

    def execute(self):
        self.model.task_gw_get_tasks(self.node)
        self.timeout = te.TaskTimeout(self.node, 6, self.model.gw)
        self.retries += 1

    def success(self, event):
        self.timeout.cancel()
        self.model.logger.info("Get tasks for node %s successfully",
            event.node.mac.hex())

    def error(self, event):
        if self.retries < self.MAX_RETRIES:
            self.execute()
        else:
            self.model.logger.info("Max retries for %s, node %s", str(self),
                self.node.mac.hex())
            self.model.reschedule_tasks(self.node)
