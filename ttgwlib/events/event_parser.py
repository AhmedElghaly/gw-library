import struct
import logging
import threading

from ttgwlib.events import mesh_events
from ttgwlib.events import model_events
from ttgwlib.events.uart_events import UartDisconnection


logger = logging.getLogger(__name__)


MESH_EVENT_OPCODES = {
    0x81: mesh_events.DeviceStarted,
    0x82: mesh_events.EchoRsp,
    0x84: mesh_events.CmdResponse,
    0x8A: mesh_events.Application,
    0xC0: mesh_events.ProvUnprovisionedReceived,
    0xC3: mesh_events.ProvCapsReceived,
    0xC6: mesh_events.ProvAuthRequest,
    0xC7: mesh_events.ProvEcdhRequest,
    0xC9: mesh_events.ProvFailed,
    0xC5: mesh_events.ProvComplete,
    0xC2: mesh_events.ProvLinkClosed,
    0xC1: mesh_events.ProvLinkEstablished,
    0xD2: mesh_events.MeshTxComplete,
}

MODEL_EVENT_OPCODES = {
    0x804A: model_events.NodeReset,
    0xC00000: model_events.WakeNotify,
    0xC30000: model_events.WakeAckSleep,
    0xC40000: model_events.WakeAckWait,
    0xC80000: model_events.WakeAckAlive,
    0xC50000: model_events.WakeReset,
    0xC00200: model_events.TempData,
    0xC10200: model_events.IaqData,
    0xC30200: model_events.IaAck,
    0xC40200: model_events.TempDataReliable,
    0xC60200: model_events.Co2Data,
    0xC80200: model_events.TempConfigAck,
    0xCA0200: model_events.TempCalibAck,
    0xCC0200: model_events.TempCalResetAck,
    0xCD0200: model_events.TempHeaterNotify,
    0xC00400: model_events.BatData,
    0xC00600: model_events.TapNotify,
    0xC20600: model_events.TapAckConf,
    0xC10800: model_events.LightAck,
    0xC00A00: model_events.DatetimeReq,
    0xC20A00: model_events.DatetimeAck,
    0xC10C00: model_events.TaskAck,
    0xC30C00: model_events.TaskDeleteAck,
    0xC50C00: model_events.TaskDeleteOpAck,
    0xC70C00: model_events.TaskData,
    0xC80C00: model_events.TaskGetTasksAck,
    0xCD0C00: model_events.TaskChangeAck,
    0xC11400: model_events.PowerAck,
    0xC01600: model_events.HwmData,
    0xC21600: model_events.HwmAck,
    0xC00E00: model_events.RssiNeighbrData,
    0xC20E00: model_events.RssiNeighbrAck,
    0xC40E00: model_events.RssiStatusAck,
    0xC50E00: model_events.RssiPing,
    0xC60E00: model_events.RssiPingAck,
    0xC11200: model_events.OtaVersionAck,
    0xC31200: model_events.OtaStatusAck,
    0xC51200: model_events.OtaStoreAck,
    0xC71200: model_events.OtaRelayAck,
    0xC11800: model_events.BeaconStartAck,
    0xC31800: model_events.BeaconStopAck,
    0xC21A00: model_events.TransportRecv,
    0xC31A00: model_events.TransportFrStart,
    0xC41A00: model_events.TransportFrData,
    0xC51A00: model_events.TransportFrEnd,
    0xC01C00: model_events.PwmtData,
    0xC21C00: model_events.PwmtConfigAck,
    0xC41C00: model_events.PwmtConvAck,
    0xC11E00: model_events.OutputDacAck,
    0xC31E00: model_events.OutputDigAck,
}


class EventParser:
    def __init__(self, gateway):
        self.gw = gateway
        self.uart = self.gw.uart
        self.event_handler = self.gw.event_handler
        self.running = True
        threading.Thread(target=self.rx_process, name='EvtParser').start()

    def rx_process(self):
        start = bytearray.fromhex("048102")
        msg = bytearray(5)
        # Ignore incoming messages until the start message is received
        while start != msg[:3]:
            msg = msg[1:5] + self.uart.get_byte()
        self.process_packet(msg)

        while self.running:
            if not self.uart.is_connected():
                event = UartDisconnection(self.gw)
                self.event_handler.add_event(event)
                self.stop()
            msg = bytearray()
            msg += self.uart.get_byte(1)
            if msg:
                while len(msg) < msg[0] + 1:
                    if not self.running:
                        return
                    msg += self.uart.get_byte(1)
                self.process_packet(msg)

    def stop(self):
        self.running = False

    def process_packet(self, msg):
        logger.log(9, f"RX: {msg.hex()}")
        try:
            event = self.deserialize(msg)
            if event:
                self.event_handler.add_event(event)
        except:
            logger.exception("Parsing error")
            raise

    def deserialize(self, data):
        opcode = data[1]
        if opcode in MESH_EVENT_OPCODES:
            return MESH_EVENT_OPCODES[opcode](data[2:], self.gw)
        if opcode == 0xD0 or opcode == 0xD1:
            return self.model_deserialize(data[2:])
        return None

    def model_deserialize(self, data):
        data_unpacked = struct.unpack("<HHHHBB6sbHI", data[0:23])
        mesh_data = {}
        mesh_data["src"] = data_unpacked[0]
        mesh_data["dst"] = data_unpacked[1]
        mesh_data["appkey_handle"] = data_unpacked[2]
        mesh_data["subnet_handle"] = data_unpacked[3]
        mesh_data["ttl"] = data_unpacked[4]
        mesh_data["adv_addr_type"] = data_unpacked[5]
        adv_addr = bytearray(data_unpacked[6])
        adv_addr.reverse()
        mesh_data["adv_addr"] = bytes(adv_addr)
        mesh_data["rssi"] = data_unpacked[7]
        mesh_data["actual_length"] = data_unpacked[8]
        mesh_data["sequence_number"] = data_unpacked[9]
        raw_model_data = data[23:] # Variable length

        # Check replay cache
        if (not self.gw.replay_cache.check_seq_number(mesh_data["src"],
                mesh_data["sequence_number"])):
            return None

        logger.log(9, f"{mesh_data['src']=}, {mesh_data['dst']=}, " +
                     f"{mesh_data['ttl']=}, {mesh_data['sequence_number']=}")

        # Check node exists
        # If addr <= 10, msg is from another gateway (transport model)
        #TODO Create some object or class to reference other gateways
        node = self.gw.node_db.get_node_by_address(mesh_data["src"])
        if node is None and mesh_data["src"] > 10:
            return model_events.UnknownNode(mesh_data, self.gw)

        opcode, model_data = self.model_get_opcode(raw_model_data)
        if opcode in MODEL_EVENT_OPCODES:
            return MODEL_EVENT_OPCODES[opcode](mesh_data, model_data, node,
                self.gw)
        return None

    def model_get_opcode(self, data):
        # Mask for opcode size in first byte: 0b00XX XXXX
        # 00/01 (1 Byte), 10 (2 Bytes), 11 (3 Bytes)
        op_format = (data[0] & 0xC0) >> 6
        if op_format == 0 or op_format == 1:
            opcode = int.from_bytes(data[0:1], "big")
            model_data = data[1:]
        elif op_format == 2:
            opcode = int.from_bytes(data[0:2], "big")
            model_data = data[2:]
        else:
            opcode = int.from_bytes(data[0:3], "big")
            model_data = data[3:]
        return opcode, model_data
