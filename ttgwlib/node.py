from enum import Enum

class Boards(Enum):
    """ This class represents a board type.
    """
    IRIS = 1
    PROMETEO = 2
    SOTER = 3
    THOR = 4
    RHEA = 5

    def is_low_power(self):
        return self == Boards.IRIS or self == Boards.SOTER

    def is_power_meter(self):
        return self == Boards.THOR


BOARD_IDS = {
    0: Boards.IRIS,
    1: Boards.IRIS,
    2: Boards.IRIS,
    6: Boards.PROMETEO,
    7: Boards.PROMETEO,
    16: Boards.IRIS,
    17: Boards.IRIS,
    20: Boards.PROMETEO,
    21: Boards.SOTER,
    24: Boards.IRIS,
    25: Boards.PROMETEO,
    28: Boards.SOTER,
    30: Boards.PROMETEO,
    31: Boards.THOR,
    32: Boards.THOR, # Power meter
    33: Boards.RHEA,
    34: Boards.THOR,
    35: Boards.IRIS,
}

BOARD_ID_NAME = {
    "iris_boardv1"       : 1,
    "iris_boardv2"       : 2,
    "iris_boardv2_1"     : 16,
    "iris_boardv3_accel" : 17,
    "iris_boardv5"       : 24,
    "iris_boardv6"       : 35,
    "prometeo_boardv1"   : 6,
    "prometeo_boardv2"   : 7,
    "prometeo_boardv3"   : 20,
    "prometeo_boardv4"   : 25,
    "prometeo_boardv5"   : 30,
    "soter_boardv1"      : 21,
    "soter_boardv2"      : 28,
    "thor_boardv1"       : 31,
    "power_meter_boardv1": 32,
    "rhea_boardv1"       : 33,
    "thor_boardv2"       : 34,
}


class Node:
    """ This class represent a Bluetooth Mesh node, and stores its
    related information.

    :ivar mac: Node mac address.
    :vartype mac: bytes[6]
    :ivar uuid: Node universal unique identifier.
    :vartype uuid: bytes[16]
    :ivar unicast_addr: Node Mesh unicast address.
    :vartype unicast_addr: integer
    :ivar devkey: Device key.
    :vartype devkey: bytes[16]
    :ivar netkey_index: Mesh subnet index.
    :vartype netkey_index: integer
    :ivar name: Node name.
    :vartype name: string
    :ivar sleep_period: Time between wake ups, in seconds.
    :vartype sleep_period: integer
    """
    def __init__(self, mac: bytes, uuid: bytes=None, unicast_addr: int=0,
            name: str="", devkey: bytes=None):
        if not uuid:
            uuid = bytes.fromhex("00000000000000000000000000000000")
        if not devkey:
            devkey = bytes.fromhex("00000000000000000000000000000000")

        self.mac = bytes(mac)
        self.uuid = uuid
        self.unicast_addr = unicast_addr
        self.name = name
        self.devkey = devkey
        self.netkey_index = 0

        self.sleep_period = 0
        self.sleep_timestamp = 0
        self.msg_timestamp = 0

    @property
    def board_id(self) -> int:
        if self.uuid:
            return int.from_bytes(self.uuid[2:4], "big")
        return 0

    def is_low_power(self) -> bool:
        if self.board_id in BOARD_IDS:
            return BOARD_IDS[self.board_id].is_low_power()
        return True

    def is_power_meter(self) -> bool:
        if self.board_id in BOARD_IDS:
            return BOARD_IDS[self.board_id].is_power_meter()
        return False

    def has_co2(self) -> bool:
        if self.board_id in BOARD_IDS:
            return BOARD_IDS[self.board_id] == Boards.SOTER
        return False

    def has_iaq(self) -> bool:
        return False

    def __str__(self):
        return self.mac.hex()

    def __repr__(self):
        return "Node " + self.mac.hex()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.mac == other.mac

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.mac)

    def to_json(self):
        return {
            "name": self.name,
            "mac": self.mac.hex(),
            "uuid": self.uuid.hex(),
            "unicast_address": self.unicast_addr,
            "devkey": self.devkey.hex(),
            "sleep_period": self.sleep_period,
            "sleep_timestamp": self.sleep_timestamp,
            "msg_timestamp": self.msg_timestamp,
        }

    @classmethod
    def from_json(cls, json):
        mac = bytes.fromhex(json.get("mac"))
        uuid = bytes.fromhex(json.get("uuid"))
        unicast_addr = json.get("unicast_address", 0)
        name = json.get("name", "")
        devkey = bytes.fromhex(json.get("devkey"))
        node = cls(mac, uuid, unicast_addr, name, devkey)
        node.sleep_period = json.get("sleep_period", 0)
        node.sleep_timestamp = json.get("sleep_timestamp", 0)
        node.msg_timestamp = json.get("msg_timestamp", 0)
        return node
