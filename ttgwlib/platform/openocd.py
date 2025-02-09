import os
import re
import time
import logging
import subprocess
import tempfile
import zipfile
from packaging import version

from ttgwlib.platform.programmer import Programmer
from ttgwlib.platform.exception import GatewayError
from ttgwlib.version import FW_VERSION


logger = logging.getLogger(__name__)


class OpenOCD(Programmer):
    FW_DIR = "/opt/gw-firmware"
    FW_IDENTIFIER = 0x9b

    def __init__(self):
        self.version = None
        self.fw_id = None
        self.initialized = False
        self.connected = False
        self.serial = "/dev/ttymxc6"

    def get_fw_version(self):
        """ Returns the device firmware version.

        :return: Firmware version.
        :rtype: str
        """
        return str(self.version)

    def get_serial_port(self):
        """ Returns the serial port.

        :return: Serial port.
        :rtype: str
        """
        return self.serial

    def init(self):
        """ Starts OpenOCD server, connects to the device, reads the firmware
        version and then disconnects from the device.
        """
        if self.initialized:
            raise GatewayError("OpenOCD already initialized")
        self.initialized = True
        self.read_fw()

    def update_fw(self):
        """ Updates the device with the lastest firmware version. Connects to
        the device, then updates the firmware and disconnects from the device.
        """
        if not self.initialized:
            raise GatewayError("OpenOCD not initialized")
        if (self.fw_id == self.FW_IDENTIFIER and
                version.parse(FW_VERSION) <= self.version):
            return
        logger.info("Updating firmware")
        time.sleep(1)
        with tempfile.TemporaryDirectory() as tmp_dir:
            for file in os.listdir(self.FW_DIR):
                if file[-4:] == ".zip":
                    with zipfile.ZipFile(f"{self.FW_DIR}/{file}") as fzip:
                        fzip.extractall(tmp_dir)
            update_cmd = [
                "openocd",
                "-f", "heimdall.cfg",
                "-c", "erase",
                "-c", f"program {tmp_dir}/sd.hex verify",
                "-c", f"program {tmp_dir}/app.hex verify",
                "-c", "rg exit"
            ]
            subprocess.run(update_cmd, capture_output=True, timeout=30,
                check=False)
        logger.debug("Update completed")

    def read_fw(self):
        """  Read device current firmware version
        """
        if not self.initialized:
            raise GatewayError("OpenOCD not initialized")

        update_cmd = [
            "openocd",
            "-f", "heimdall.cfg",
            "-c", "init",
            "-c", "mdw 0x10001080 4",
            "-c", "exit"
        ]
        ret = subprocess.run(update_cmd, capture_output=True, timeout=30,
            check=False)
        if ret.returncode != 0:
            raise GatewayError("Unable to read firmware version")

        lines = ret.stderr.decode().splitlines()

        for l in lines:
            if l.startswith("0x10001080:"):
                mem_filter = "0x10001080: (\w+) (\w+) (\w+) (\w+)"
                m = re.search(mem_filter, l)
                self.fw_id, major, minor, fix = list(map(lambda x: int(x, 16),
                        m.groups()))
                self.version = version.parse(f"{major}.{minor}.{fix}")
                logger.debug("FW version: " + str(self.version))
                return

    def hard_reset(self):
        """ Hard resets the device.
        """
        if not self.initialized:
            raise GatewayError("OpenOCD not initialized")
        reset_cmd = [
            "openocd",
            "-f", "heimdall.cfg",
            "-c", "rg exit"
        ]
        subprocess.run(reset_cmd, capture_output=True, timeout=10, check=False)
        logger.debug("Hard reset device")
