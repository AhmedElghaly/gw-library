import logging
from typing import Dict
import zipfile
import json
import re
from packaging import version

import ttgwlib.commands as cmds

from ttgwlib.node import BOARD_ID_NAME


class OtaType:
    OTA_TYPE_BOOTLOADER = 0
    OTA_TYPE_APPLICATION = 1
    OTA_TYPE_SOFTDEVICE = 2


class OtaHelper:
    SERIAL_DATA_LENGTH = 128 # 16 words

    def __init__(self, uart):
        self.logger = logging.getLogger(__name__)
        self.uart = uart

    def enable_mesh(self):
        msg = cmds.EnableSoftdevice()
        self.uart.send_msg(msg.serialize())
        msg = cmds.EnableMesh()
        self.uart.send_msg(msg.serialize())

    def disable_mesh(self):
        msg = cmds.DisableMesh()
        self.uart.send_msg(msg.serialize())
        msg = cmds.DisableSoftdevice()
        self.uart.send_msg(msg.serialize())

    def send_update(self):
        self.disable_mesh()
        msg = cmds.UpdateSend()
        self.uart.send_msg(msg.serialize())
        self.enable_mesh()

    def copy_update(self, hex_data: Dict[int, int], signature: str):
        signature = bytes.fromhex(signature)
        start_address = min(list(hex_data.keys()))
        size = len(hex_data)

        self.disable_mesh()

        # Start packet
        msg = cmds.UpdateStartData(start_address, size, signature)
        self.uart.send_msg(msg.serialize())

        for address in range(start_address, start_address+size+1,
                self.SERIAL_DATA_LENGTH):
            bin_data = bytearray()
            for n in range(self.SERIAL_DATA_LENGTH):
                value = hex_data.get(address+n)
                if value is None:
                    break
                bin_data.append(value)
            msg = cmds.UpdateBinData(address, bin_data)
            self.uart.send_msg(msg.serialize())

        self.enable_mesh()

    def update_status(self):
        msg = cmds.UpdateStatus()
        self.uart.send_msg(msg.serialize())

    def install_update(self, update_type):
        msg = cmds.UpdateInstall(update_type)
        self.uart.send_msg(msg.serialize())

    def hex_load(self, hex_raw_data: str) -> Dict[int, int]:
        hex_data = {}

        address_prefix = 0
        next_address = 0
        trailing_address = 0

        for line in hex_raw_data.splitlines():
            if line[7:9] == "02":
                address_prefix = int(line[9:13], base=16) << 4

            elif line[7:9] == "04":
                address_prefix = int(line[9:13], base=16) << 16

            elif line[7:9] == "00":
                address_base = int(line[3:7], base=16)
                address = address_prefix + address_base
                if (next_address != address and next_address):
                    break

                line_data = bytes.fromhex(line[9:-2])
                for i in range(len(line_data)):
                    hex_data[address+i] = line_data[i]
                    if line_data[i] != 0xFF:
                        trailing_address = address+i
                next_address = address + len(line_data)

        key_list = list(hex_data.keys())
        for key in key_list:
            if key > trailing_address:
                del hex_data[key]

        return hex_data

    def add_softdevice(self):
        pass

    def load_ota(self, ota_zip: str, ota_type: int, copy: bool=True):
        if ota_type == OtaType.OTA_TYPE_BOOTLOADER:
            hex_file = "bl.hex"
            sign_field = "bootloader_sign"
        else:
            hex_file = "app.hex"
            sign_field = "app_sign"

        with zipfile.ZipFile(ota_zip, 'r') as archive:
            ota_data = json.loads(archive.read("ota_data.json"))
            app_hex = archive.read(hex_file).decode()
            if ota_type == OtaType.OTA_TYPE_SOFTDEVICE:
                sd_hex = archive.read("sd.hex").decode()

        hex_data = self.hex_load(app_hex)
        if ota_type == OtaType.OTA_TYPE_SOFTDEVICE:
            hex_sd = self.hex_load(sd_hex)
            for i in range(max(hex_sd)+1, min(hex_data)):
                hex_sd[i] = 0xFF
            hex_sd.update(hex_data)
            hex_data = hex_sd
            sign_field = "app_sd_sign"

        data = {}
        data["sign"] = ota_data[sign_field]

        addresses = list(hex_data.keys())
        addresses.sort()
        data["start_address"] = addresses[0]
        data["size"] = len(hex_data)
        if ota_type == OtaType.OTA_TYPE_BOOTLOADER:
            m = re.match("^[0-9.]+-?\w*\.?\d*", ota_data["bootloader_version"])
        else:
            m = re.match("^[0-9.]+-?\w*\.?\d*", ota_data["app_version"])

        if m:
            ota_ver = version.parse(m[0])
        else:
            ota_ver = version.parse("0.0.0")

        if ota_data["board"] in BOARD_ID_NAME:
            board_id = BOARD_ID_NAME[ota_data["board"]]
        else:
            board_id = 0
            self.logger.warning("Unknown board name")

        data["major"] = ota_ver.major
        data["minor"] = ota_ver.minor
        data["fix"] = ota_ver.micro
        data["board_id"] = board_id
        data["sd_version"] = int(ota_data["softdevice_version"], 16)
        if copy:
            self.copy_update(hex_data, data["sign"])

        return data
