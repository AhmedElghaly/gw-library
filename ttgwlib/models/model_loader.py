from ttgwlib.models.task_queue import TaskQueue
from ttgwlib.models.config_client import ConfigurationClient
from ttgwlib.models.nrf_temp import NrfTemp
from ttgwlib.models.battery import Battery
from ttgwlib.models.tap import Tap
from ttgwlib.models.light import Light
from ttgwlib.models.power import Power
from ttgwlib.models.hwm import Hwm
from ttgwlib.models.rssi import Rssi
from ttgwlib.models.datetime_gw import Datetime
from ttgwlib.models.task_gw import TaskGw
from ttgwlib.models.wake_up import WakeUp
from ttgwlib.models.ota import Ota
from ttgwlib.models.beacon import Beacon
from ttgwlib.models.pwmt import Pwmt
from ttgwlib.models.output import Output
from ttgwlib.models.transport import TransportModel


class ModelLoader:
    def __init__(self, gateway):
        self.task_queue = TaskQueue(gateway)
        self.config = ConfigurationClient(gateway)
        self.nrf_temp = NrfTemp(gateway)
        self.battery = Battery(gateway)
        self.tap = Tap(gateway)
        self.light = Light(gateway)
        self.power = Power(gateway)
        self.hwm = Hwm(gateway)
        self.rssi = Rssi(gateway)
        self.datetime = Datetime(gateway)
        self.task_gw = TaskGw(gateway)
        self.wake_up = WakeUp(gateway)
        self.ota = Ota(gateway)
        self.beacon = Beacon(gateway)
        self.pwmt = Pwmt(gateway)
        self.output = Output(gateway)
        self.transport = TransportModel(gateway)
