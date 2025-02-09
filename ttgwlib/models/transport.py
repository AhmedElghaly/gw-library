import math
import struct
import logging

from ttgwlib.models.model import Model
from ttgwlib.events.event import EventType
from ttgwlib.events.model_events import TransportRecv


FRAG_SIZE = 5


class TransportModel(Model):
    MODEL_ID = 0x001A
    VENDOR_ID = MODEL_ID

    SEND = Model.opcode_to_bytes(0xC2, VENDOR_ID)
    FRAGMENT_START = Model.opcode_to_bytes(0xC3, VENDOR_ID)
    FRAGMENT_DATA = Model.opcode_to_bytes(0xC4, VENDOR_ID)
    FRAGMENT_END = Model.opcode_to_bytes(0xC5, VENDOR_ID)

    def __init__(self, gateway):
        self.gw = gateway
        self.logger = logging.getLogger(__name__)
        handlers = [
            self.data_handler,
        ]

        self.frpkt = {}
        super().__init__(gateway, handlers)

    def send_msg(self, addr, data):
        if not isinstance(data, bytearray) and not isinstance(data, bytes):
            raise TypeError("Data should be 'bytearray' type instead " +
                f"of {type(data)}.")

        if len(data) <= 7:
            msg = bytearray()
            msg += self.SEND
            msg += data
            self.send_addr(msg, addr)

        else:
            self.send_fr_start(addr, len(data))
            self.send_fr_data(addr, data)
            self.send_fr_end(addr, data)

    def data_handler(self, event):
        if event.event_type == EventType.TRANSPORT_FR_START:
            pkt_len = event.data["len"]
            self.frpkt[event.data["src"]] = FragmentedPkt(pkt_len)

        elif event.event_type == EventType.TRANSPORT_FR_DATA:
            tr_data = event.data["data"]
            seq_n = event.data["seq"]
            self.frpkt[event.data["src"]].add_data(seq_n, tr_data)

        elif event.event_type == EventType.TRANSPORT_FR_END:
            check = event.data["sum"]
            frag_packet = self.frpkt[event.data["src"]]
            if frag_packet.is_complete() and frag_packet.checksum(check):
                rx_data = frag_packet.get_data()
                mesh_data = {
                    "rssi": event.data["rssi"],
                    "ttl": event.data["ttl"],
                    "src": event.data["src"]
                }
                recv_event = TransportRecv(mesh_data, rx_data, None, self.gw)
                self.gw.event_handler.add_event(recv_event)
            else:
                self.logger.warning("Fragment end error")

    def send_fr_start(self, addr, length):
        msg = bytearray()
        msg += self.FRAGMENT_START
        msg += struct.pack("<H", length)
        self.send_addr(msg, addr, True)

    def send_fr_end(self, addr, data):
        msg = bytearray()
        msg += self.FRAGMENT_END
        msg += struct.pack("<6p", bytearray([1,2,3,4,5,6]))
        self.send_addr(msg, addr, True)

    def send_fr_data(self, addr, data):
        n_seq = math.ceil(len(data)/FRAG_SIZE)
        for seq in range(n_seq):
            msg = bytearray()
            msg += self.FRAGMENT_DATA
            msg += struct.pack("<H", seq)
            start = seq * FRAG_SIZE
            end = (seq + 1) * FRAG_SIZE

            if end >= len(data):
                end = len(data)

            msg += data[start:end]
            self.send_addr(msg, addr, True)


class FragmentedPkt:
    def __init__(self, length):
        self.length = length
        self.packets = [[] for i in range(math.ceil(length/FRAG_SIZE))]

    def add_data(self, seq, data):
        if seq >= self.length:
            raise ValueError(f"Sequence {seq} outside range"
                + f" {len(self.packets)}")

        if len(self.packets[seq]) > 0:
            return

        self.packets[seq] = list(data)

    def is_complete(self):
        for p in self.packets:
            if not p:
                return False
        return True

    def checksum(self, chksum):
        return True

    def get_data(self):
        if not self.is_complete():
            return None

        data_bytes = bytearray()

        for p in self.packets:
            data_bytes += bytearray(p)

        return data_bytes
