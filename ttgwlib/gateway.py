"""
:mod:`~ttgwlib.gateway`
=========================

This module contains the class :class:`Gateway`, which is the main way to
interact with the Bluetooth Mesh net. The actual Bluetooth communication is
made by a Nordic nRF52 microcontroller which acts both as provisioner and as
gateway. The microcontroller is managed by this library through serial
interface.
"""
import time

from ttgwlib.version import VERSION
from ttgwlib.uart import Uart
from ttgwlib.uart_socket import UartSocket
from ttgwlib.tx_manager import TxManager
from ttgwlib.events.event_handler import EventHandler
from ttgwlib.events.replay_cache import ReplayCache
from ttgwlib.events.event_parser import EventParser
from ttgwlib.ota_helper import OtaHelper
from ttgwlib.provisioning.prov_manager import ProvManager
from ttgwlib.dev_manager import DeviceManager
from ttgwlib.models.model_loader import ModelLoader
from ttgwlib.platform.board import Platform
from ttgwlib.passthrough import Passthrough
from ttgwlib.whitelist import Whitelist


class Gateway:
    """ This class is the main library API to manage the Bluetooth Mesh net.

    It is tasked with initializing an controlling the microcontroller, and to
    process any event in the net, like receiving the data or adding, removing
    and configuring nodes.

    It also mantains the needed information about the Mesh and the nodes, and
    communicates with the config database to store the new information. This
    database must be implemented by the user following the abstract class
    provided by the library. For more info, see
    :class:`~ttgwlib.database.node_database.NodeDatabase`.

    The constructor does not initialize the hardware. That is done through the
    function :func:`init`. Equally, to stop the hardware, before quitting the
    application the function :func:`close` should be called to prevent from
    serial syncronization errors.
    """
    def __init__(self):
        self.listener = False
        self.prov_mode = False
        self.config_mode = None
        self.node_db = None
        self.uart = None
        self.event_handler = None
        self.replay_cache = None
        self.event_parser = None
        self.ota_helper = None
        self.prov_man = None
        self.models = None
        self.dev_manager = None
        self.tx_manager = None
        self.programmer = None
        self.passthrough = None
        self.whitelist = None
        self.remote = None

    def init(self, config):
        """ Initializes all needed objects and the microcontroller.

        :param config: Gateway library configuration. Look to its
            documentation for more info.
        :type: :class:`~ttgwlib.config.Config`

        :raises SerialException: If it can not connect to the provided port.
        :raises GatewayError: Error connecting to the microcontroller.
        """
        self.prov_mode = config.prov_mode
        self.config_mode = config.config_mode
        self.node_db = config.node_db
        self.whitelist = Whitelist(self)
        self.config_platform(config.platform, config.port)

        self.event_handler = EventHandler()
        self.ota_helper = OtaHelper(self.uart)
        self.replay_cache = ReplayCache()
        self.event_parser = EventParser(self)

        self.prov_man = ProvManager(self)
        self.models = ModelLoader(self)

        self.dev_manager = DeviceManager(self, config.seq_number_file,
            self.remote)
        self.tx_manager = TxManager(self)
        if not self.remote:
            self.dev_manager.start_device()

        if config.config_cb:
            self.models.task_queue.set_confifuration_cb(config.config_cb)

    def init_passthrough(self, config):
        """
        Initializes the gateway in passthrough mode, which allows it to forward
        data between a local UART port and a remote server using a secure TCP
        connection.

        :param config: Gateway library passthrough configuration. Look to its
            documentation for more info.
        :type: :class:`~ttgwlib.config.ConfigPassthrough`
        """
        self.event_handler = EventHandler()
        self.config_platform(config.platform, config.port)
        self.passthrough = Passthrough(config.address, config.tcp_port,
            self.uart, self.programmer)
        self.passthrough.set_ca_cert(config.ca_cert)
        self.passthrough.set_client_auth(config.client_cert, config.client_key)
        self.passthrough.start()

    def close(self):
        """ Stops the microcontroller and the background threads.
        Should be called before exiting the application.
        """
        if self.dev_manager is not None and self.dev_manager.dev_started:
            self.stop_scan()
            if isinstance(self.uart, Uart):
                self.dev_manager.stop_device()
            self.uart.stop()
            self.event_parser.stop()
            self.event_handler.stop()
            self.tx_manager.stop()
        elif self.passthrough is not None:
            self.passthrough.stop()

    def config_platform(self, platform, port):
        """ Configurates the platform, which includes the uart, the programmer,
        and the firmware update.
        """
        if isinstance(platform, str):
            platform = Platform.from_string(platform)

        if platform == Platform.DESKTOP:
            from ttgwlib.platform.jlink import JLink
            self.programmer = JLink()
        elif platform in (Platform.HEIMDALL_V1, Platform.HEIMDALL_V2):
            from ttgwlib.platform.openocd import OpenOCD
            self.programmer = OpenOCD()

        if platform == Platform.CLOUD:
            self.uart = UartSocket(port)
            self.remote = True
        else:
            self.programmer.init()
            self.programmer.update_fw()
            if not port:
                port = self.programmer.get_serial_port()
            self.uart = Uart(port)
            self.remote = False

    def reset(self):
        """ Resets the microcontroller.
        """
        self.dev_manager.start_device()

    def check_connection(self):
        """ Checks the uart connection with the microcontroller.

        :return: True if the connection is alive, false otherwise.
        :rtype: bool
        """
        return self.dev_manager.check_connection()

    def add_event_handler(self, handler):
        """ Adds an event handler that will be called every time a new
        event is generated by the library. The handler must be a
        Callable object that receives a
        :class:`~ttgwlib.events.event.Event` object as the only
        parameter. It may want to filter the event type to process
        only the events wanted.

        :param handler: Handler to be added.
        :type handler: Callable
        """
        self.event_handler.add_handler(handler)

    def remove_event_handler(self, handler):
        """ Removes a previosly added event handler.

        :param handler: Handler to be removed.
        :type handler: Callable
        """
        self.event_handler.remove_handler(handler)

    def get_fw_version(self):
        if self.programmer:
            return self.programmer.get_fw_version()
        return ""

    def get_status(self):
        """ Returns a dictionary with the gateway and Mesh network
        status. Its fields are:

        lib_version: string
        fw_version: string
        scanning: boolean
        provisioning: boolean
        listener: boolean
        nodes: integer
        max_nodes: integer
        unicast_addr: integer
        netkey: string

        :return: Status dictionry.
        :rtype: dict
        """
        return {
            "lib_version": VERSION,
            "fw_version": self.get_fw_version(),
            "scanning": self.prov_man.scanning,
            "provisioning": self.prov_man.provisioning,
            "nodes": len(self.node_db.get_nodes()),
            "listener": self.listener,
            "max_nodes": self.dev_manager.cache_size,
            "unicast_addr": self.node_db.get_address(),
            "netkey": self.node_db.get_netkey().hex()
        }

    def set_listener(self, on):
        """ Activates/Deactivates listener mode, used to listen with
        more than one gateway in the same Mesh net, to avoid
        collisions while managing it. A gateway in this mode only
        listens for incoming packets, without sending anything.

        :param on: Activates listener mode.
        :type on: bool
        """
        self.listener = bool(on)

    def is_listener(self):
        """ Gets the listener status.

        :return: Listener active.
        :rtype: bool
        """
        return self.listener

    def is_provisioner_mode(self):
        """ Get if the gateway is in provisioner mode (no node config).
        It can only be activate on startup.

        :return: Whether provisioner mode is active.
        :rtype: bool
        """
        return self.prov_mode

    def get_config_mode(self):
        """ Get the configuration mode to configure the node tasks.

        :return: Configuration mode (legacy, default).
        :rtype: str
        """
        return self.config_mode

    def get_sleep_time(self):
        """ Returns the deafult sleep time, applied to every node after
        it is configured.

        :return: The actual default sleep time, in seconds.
        :rtype: int
        """
        return self.models.wake_up.sleep_time

    def set_sleep_time(self, sleep_time):
        """ Sets the deafult sleep time, applied to every node after
        it is configured. If set to 0, every node will remain awake.

        :param sleep_time: Default sleep time, in seconds.
        :type sleep_time: int
        """
        self.models.wake_up.sleep_time = int(sleep_time)

    def start_scan(self, uuid_filters=None, mac_filters=None, timeout=0,
            one=False):
        """ Starts detection of unprovisioned nodes.

        If a discovered unprovisioned device passes any of the given filters,
        it will be automatically provisioned and configured. Only one node can
        be provisioned at a time, and while one is being provisioned, no more
        nodes will be passed to the filter. Once the node is configured, the
        scanning starts again. Although the filters are optional, if none is
        given, no node will be provisioned.

        The filters (both uuid and mac) should be a list of strings. This
        strings can be shorter than the uuid (16 bytes / 32 letters) or mac
        (6 bytes / 12 letters) values themselves. In this case, only the most
        significant bits will be compared, e.g., if the uuid filter provided is
        DA510001FFFFFFFF, a node with uuid DA510001FFFFFFFF9B1979D4D43D6268
        will pass the filter and be provisioned.

        A timeout can be provided, to automatically stop scanning after that
        time. If set to 0, the scanning last indefinitely, until
        :func:`stop_scan` is called.

        :param uuid_filters: UUID filters to apply to discovered nodes.
        :type uuid_filters: list of string, optional
        :param mac_filters: MAC filters to apply to discovered nodes.
        :type mac_filters: list of string, optional
        :param timeout: Time to scan, in seconds.
        :type timeout: integer, optional
        """
        if uuid_filters is None:
            uuid_filters = []
        if mac_filters is None:
            mac_filters = []
        self.prov_man.start_scan(uuid_filters, mac_filters, timeout, one)

    def stop_scan(self):
        """ Stops detection of unprovisioned nodes.
        """
        self.prov_man.stop_scan()

    def send_msg(self, unicast_addr, msg):
        """ Sends the message msg to the node with the specified unicast
        address. Use to communicate between gateways.

        :param unicast_addr: Receiver unicast address.
        :type unicast_addr: int
        :param msg: Data to be sent.
        :type msg: bytes
        """
        self.models.transport.send_msg(unicast_addr, msg)

    def get_neighbr_rssi(self, node):
        """ Get neighbour rssi messages for the given node.

        :param node: Node from which you want to receive the data.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.rssi.get_neighbr_rssi_data(node)

    def get_status_rssi(self, node):
        """ Get the rssi mean for the given node.

        :param node: Node from which you want to receive the data.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.rssi.get_status_rssi_data(node)

    def ping_to_node(self, node):
        """ Send ping to a giveng node.

        :param node: Node from which you want to receive the data.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.rssi.ping_to_node(node)

    def get_pending_tasks(self, node):
        """ Get the scheduled task for the given node

        :param node: Node tasks are to be cancelled.
        :type node: :class:`~ttgwlib.node.Node`

        :return: List with the scheduled tasks.
        :rtype: list of str
        """
        return [str(t) for t in self.models.task_queue.get_tasks(node)]

    def cancel_tasks(self, node):
        """ Cancel any scheduled tasks for the given node.

        :param node: Node tasks are to be cancelled.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.task_queue.cancel_tasks(node)

    def get_node_tasks(self, node):
        """ Get the active tasks for the given node

        :param node: Node task from which you want to receive the tasks.
        :type node: :class:`~ttgwlib.node.Node`

        :return: List with the node tasks.
        :rtype: list of str
        """
        self.models.task_gw.get_tasks(node)

    def get_node_selftest(self, node):
        """ Get the selftests for the given node

        :param node: Node from which you want to receive the selftest.
        :type node: :class:`~ttgwlib.node.Node`

        :return: List with the node sensors status.
        :rtype: list of str
        """
        self.models.hwm.get_selftest_data(node)

    def get_node_ota_status(self, node):
        """ Get the ota status for the given node

        :param node: Node task from which you want to receive the ota status.
        :type node: :class:`~ttgwlib.node.Node`

        :return: Ota status.
        :rtype: int
        """
        self.models.ota.status(node)

    def reset_node(self, node):
        """ Resets a node. The node must be awake in order to receive the
        message. If the node acknowledges the operation, it is removed from the
        Mesh.

        :param node: Node to be reset.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.config.reset_node(node)

    def set_rate(self, node, rate):
        """ Changes the NRFTemp model sending rate of the given node.

        :param node: Node whose rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New sending rate, in seconds.
        :type rate: integer
        """
        self.models.nrf_temp.set_nrftemp_rate(node, rate)

    def set_rate_legacy(self, node, rate):
        """ Changes the NRFTemp model sending rate of the given node (legacy).

        :param node: Node whose rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New sending rate, in seconds.
        :type rate: integer
        """
        self.models.nrf_temp.set_nrftemp_rate_legacy(node, rate)

    def set_ia(self, node, status, skip):
        """ Changes the NRFTemp model intelligence config of the given node.

        :param node: Node whose ia config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param status: IA status (1:on/0:off).
        :type status: integer
        :param skip: Max skip values.
        :type skip: integer

        :raises ValueError: Incorrect parameter value.
        """
        if status not in (0, 1):
            raise ValueError("Status must be 0 (off) or 1 (on).")
        self.models.nrf_temp.set_ia(node, status, skip)

    def set_temp_mode(self, node, mode):
        """ Changes the NRFTemp model intelligence config of the given node.

        :param node: Node whose ia config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param mode: Sensor mode (only SHT4X supported).
        :type mode: integer

        :raises ValueError: Incorrect parameter value.
        """
        available_modes = self.models.nrf_temp.get_config_modes()
        if mode not in available_modes:
            raise ValueError(f"Mode must be {available_modes}")
        self.models.nrf_temp.set_configuration(node, mode)

    def set_calibration(self, node, temp_offset, humd_offset, press_offset):
        """ Changes the NRFTemp model intelligence config of the given node.

        :param node: Node whose ia config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param temp_offset: Temperature offset (ºC)
        :type temp_offset: integer
        :param humd_offset: Humidity offset (%HR)
        :type humd_offset: integer
        :param press_offset: Press offset (hPa)
        :type press_offset: integer

        :raises ValueError: Incorrect parameter value.
        """
        self.models.nrf_temp.set_calibration(node, temp_offset, humd_offset,
                press_offset)

    def reset_calibration(self, node, temp, humd, press):
        """ Changes the NRFTemp model intelligence config of the given node.

        :param node: Node whose ia config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param temp: Temperature
        :type temp_offset: bool
        :param humd: Humidity
        :type humd_offset: bool
        :param press: Press
        :type press_offset: bool

        :raises ValueError: Incorrect parameter value.
        """
        self.models.nrf_temp.reset_calibration(node, temp, humd, press)

    def set_iaq_rate(self, node, rate):
        """ Changes the NRFTemp model sending IAQ rate of the given node.

        :param node: Node whose IAQ rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New IAQ sending rate, in seconds.
        :type rate: integer
        """
        self.models.nrf_temp.set_iaq_rate(node, rate)

    def set_iaq_rate_legacy(self, node, rate):
        """ Changes the NRFTemp model sending IAQ rate of the given node
        (legacy).

        :param node: Node whose IAQ rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New IAQ sending rate, in seconds.
        :type rate: integer
        """
        self.models.nrf_temp.set_iaq_rate_legacy(node, rate)

    def set_co2_rate(self, node, rate):
        """ Changes the NRFTemp model sending CO2 rate of the given node.

        :param node: Node whose CO2 rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New CO2 sending rate, in seconds.
        :type rate: integer
        """
        self.models.nrf_temp.set_co2_rate(node, rate)

    def set_co2_rate_legacy(self, node, rate):
        """ Changes the NRFTemp model sending CO2 rate of the given node
        (legacy).

        :param node: Node whose CO2 rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New CO2 sending rate, in seconds.
        :type rate: integer
        """
        self.models.nrf_temp.set_co2_rate_legacy(node, rate)

    def set_pwmt_rate(self, node, rate):
        """ Changes the pwmt model sending power meter rate of the given
        node.

        :param node: Node whose power meter rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New power meter sending rate, in seconds.
        :type rate: integer
        """
        self.models.pwmt.set_pwmt_rate(node, rate)

    def set_pwmt_rate_legacy(self, node, rate):
        """ Changes the pwmt model sending power meter rate of the given
        node (legacy).

        :param node: Node whose power meter rate is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New power meter sending rate, in seconds.
        :type rate: integer
        """
        self.models.pwmt.set_pwmt_rate_legacy(node, rate)

    def set_pwmt_conf(self, node, phases, stats, values_ph, values_tot):
        """ Changes the pwmt model config of the given node.

        :param node: Node whose pwmt config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param phases: Phases to receive (TOT|L1|L2|L3).
        :type phases: integer
        :param stats: Stats to receive (avg|max|min).
        :type stats: integer
        :param values_ph: Phase values to receive (VIF|Ppf|QSph|E).
        :type values_ph: integer
        :param values_tot: Total values to receive (PQS|phph|vph|E).
        :type values_tot: integer

        :raises ValueError: Incorrect parameter value.
        """
        if not node.is_power_meter():
            return
        if phases < 0 or phases > 0b1111:
            raise ValueError("Incorrect phases to receive value. " +
                "(TOT|L1|L2|L3)")
        if stats < 0 or stats > 0b111:
            raise ValueError("Incorrect stats to receive value (avg|max|min)")
        if values_ph < 0 or values_ph > 0b1111:
            raise ValueError("Incorrect phase values to receive value. " +
                "(VIF|Ppf|QSph|E)")
        if values_tot < 0 or values_tot > 255:
            raise ValueError("Incorrect total values to receive value." +
                "(PQS|phph|vph|E)")
        self.models.pwmt.set_pwmt_conf(node, phases, stats, values_ph,
            values_tot)

    def set_pwmt_conv(self, node, kv, ki):
        """ Changes the pwmt channels conversion factor of the given node.

        :param node: Node whose pwmt config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param kv: New votage conversion factor (x1000).
        :type kv: integer
        :param ki: New current conversion factor (x1000).
        :type ki: integer

        :raises ValueError: Incorrect parameter value.
        """
        if not node.is_power_meter():
            return
        if kv < 0 or kv > 0xFFFFFFF:
            raise ValueError("Invalid kv")
        if ki < 0 or ki > 0xFFFFFFF:
            raise ValueError("Invalid ki")
        self.models.pwmt.set_pwmt_conv(node, kv, ki)

    def set_dac_output(self, node, value):
        """ Sets the DAC output of the given node.

        :param node: Node whose DAC output is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param value: Value of the DAC output. 0-1 (float)
        :type value: integer
        """
        self.models.output.set_dac(node, value)

    def set_digital_output(self, node, status):
        """ Sets the digital output of the given node.

        :param node: Node whose ia config is to be changed.
        :type node: :class:`~ttgwlib.node.Node`
        :param status: Status of the digital output. 0 (clear), 1 (set)
        :type status: integer
        """
        self.models.output.set_digital(node, status)

    def set_accel(self, node, state):
        """ Changes the Tap model accelerometer state of the given node.

        :param node: Node whose accel is being configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param rate: New accel state: 0 (off), 1 (on), 2 (on with colors).
        :type rate: boolean

        :raises ValueError: Incorrect parameter value.
        """
        if state in (0, 1, 2):
            self.models.tap.set_accel_state(node, state)
        else:
            raise ValueError("Invalid state")

    def set_led(self, node, color):
        """ Sets a LED for Light model of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param color: Led color. Format should be #RRGGBB.

        :raises ValueError: Incorrect parameter value.
        """
        if (not color.startswith("#")) or (len(color) != 7):
            raise ValueError("Color format should be #RRGGBB.")
        self.models.light.set_led(node, color)

    def set_power(self, node, radio_power, dcdc_mode):
        """ Changes the Power configuration of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param radio_power: Radio power (2 - High, 1 - Med, 0 - Low).
        :param dcdc_mode: DCDC mode (1 - Enabled, 0 - Disabled).

        :raises ValueError: Incorrect parameter value.
        """
        if radio_power not in (0, 1, 2):
            raise ValueError("Radio power should be 2 (high), 1 (med) or 0"
                + " (low).")
        if radio_power not in (0, 1):
            raise ValueError("DCDC mode should be 1 (enabled) or 0 (disabled).")

        self.models.power.set_power(node, radio_power, dcdc_mode)

    def set_datetime(self, node):
        """ Sets node datetime reference.

        :param node: Node to send the datetime to.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.datetime.datetime_send_datetime(node)

    def config_task(self, node, opcode, period, wait_time=0):
        """ Sets a new config task.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param opcode: Existing opcode for the new task.
        :param period: Period in seconds of the task to be scheduled.
            0 if not periodic.
        :param wait_time: Seconds to wait until first execution.
        :type wait_time: integer
        """
        self.change_task(node, opcode, int(time.time()) + wait_time, period, 0)

    def config_task_legacy(self, node, opcode, period, wait_time=0):
        """ Sets a new config task (legacy).

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param opcode: Existing opcode for the new task.
        :param period: Period in seconds of the task to be scheduled.
            0 if not periodic.
        :param wait_time: Seconds to wait until first execution.
        :type wait_time: integer
        """
        self.set_task(node, opcode, int(time.time()) + wait_time, period, 0)

    def node_reboot(self, node):
        self.models.task_gw.task_gw_conf_mono(node, 9, 1000, 0)

    def set_task(self, node, opcode, date_event, period, task_type):
        """ Sets a new task for TaskGw model of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param opcode: Existing opcode for the new task.
        :type opcode: integer
        :param date_event: Date and time in seconds of the task to be
            scheduled.
        :type state: integer
        :param period: Period in seconds of the task to be scheduled.
            0 if not periodic.
        :param task_type: Task type of the task to be scheduled.
            0 if monotonic, 1 if realtime.
        """
        self.models.task_gw.new_task(node, opcode, date_event, period,
            task_type)

    def change_task(self, node, opcode, date_event, period, task_type):
        """ Changes a task for TaskGw model of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param opcode: Existing opcode for the new task.
        :type opcode: integer
        :param date_event: Date and time in seconds of the task to be
            scheduled.
        :type state: integer
        :param period: Period in seconds of the task to be scheduled.
            0 if not periodic.
        :param task_type: Task type of the task to be scheduled.
            0 if monotonic, 1 if realtime.
        """
        self.models.task_gw.change_task(node, opcode, date_event, period,
            task_type)

    def get_configured_tasks(self, node):
        """ Gets configured tasks for TaskGw model of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        """
        return self.models.task_gw.get_configured_tasks(node)

    def delete_task(self, node, index):
        """ Deletes an existing task for TaskGw model of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param index: Index of the task to be deleted.
        :type index: integer
        """
        self.models.task_gw.delete_task(node, index)

    def delete_task_op(self, node, opcode):
        """ Deletes an existing task for TaskGw model of the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param opcode: Opcode of the tasks to be deleted.
        :type opcode: integer
        """
        self.models.task_gw.delete_task_op(node, opcode)

    def start_node_beacon(self, node, period_ms):
        """ Starts BLE beacon for the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        :param period_ms: Beacon period in miliseconds (between 20ms and 10.24s)
        :type period_ms: integer
        """
        self.models.beacon.start_beacon(node, period_ms)

    def stop_node_beacon(self, node):
        """ Starts BLE beacon for the given node.

        :param node: Node to be configured.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.models.beacon.stop_beacon(node)

    def add_node_to_whitelist(self, node):
        """ Adds a node to the whitelist.

        :param node: Node to be added.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.whitelist.add_node(node)

    def remove_node_from_whitelist(self, node):
        """ Removes a node from the whitelist.

        :param node: Node to be added.
        :type node: :class:`~ttgwlib.node.Node`
        """
        self.whitelist.remove_node(node)

    def is_node_in_whitelist(self, node):
        """
        Check if a node is in the whitelist.

        :param node: Node to be added.
        :type node: :class:`~ttgwlib.node.Node`
        """
        return self.whitelist.is_node_in_whitelist(node)

    def get_whitelist_nodes(self):
        """
        Get the list of nodes in the whitelist.
        """
        return self.whitelist.get_nodes()

    def is_passthrough_connected(self):
        """
        Check if the passthrough connection is up.
        """
        if self.passthrough:
            return self.passthrough.is_connected()
        return False
