import os
import sys
import re
import time
import logging
from packaging import version

import pylink

from ttgwlib.platform import s3_helper
from ttgwlib.platform.programmer import Programmer
from ttgwlib.platform.exception import GatewayError
from ttgwlib.version import FW_VERSION


logger = logging.getLogger(__name__)


class JLink(Programmer):
    FW_IDENTIFIER = 0x9b
    FW_MAJOR = int(FW_VERSION[0])
    FW_MINOR = int(FW_VERSION[2])
    FW_FIX = int(FW_VERSION[4])
    BOARD = "pca10040"

    def __init__(self):
        self.version = None
        self.serial = None
        self.dev = None
        self.fw_id = None
        self.jlink = pylink.JLink(log=self._supress_log,
            detailed_log=self._supress_log, error=self._supress_log,
            warn=self._supress_log)

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
        return os.path.realpath(self.dev)

    def init(self):
        """ Looks for connected gateway devices and reads the firmware version.
        """
        self.scan_devices()
        self.read_fw_version()

    def update_fw(self):
        """ Updates firmware to the lastest version.
        """
        if (self.fw_id != self.FW_IDENTIFIER or
                version.parse(FW_VERSION) > self.version):
            logger.info("Updating device")
            self.flash()
            time.sleep(2)
            self.version = version.parse(FW_VERSION)

    def scan_devices(self):
        """ Looks for connected gateway devices.
        """
        if sys.platform.startswith("linux"):
            jlink_regex = re.compile(r"....SEGGER_J-Link....(\d{9}).*")
            dev_dir = "/dev/serial/by-id"
        elif sys.platform.startswith("darwin"):
            jlink_regex = re.compile(r"tty.usbmodem000(\d{9}).*")
            dev_dir = "/dev"
        else:
            # Other platforms are not currently supported
            raise GatewayError(f"Unsupported system {sys.platform}")
        try:
            matches = [jlink_regex.match(f) for f in os.listdir(dev_dir)]
        except FileNotFoundError as e:
            raise GatewayError("Gateway not found") from e
        matches = [m for m in matches if m]
        jlink_target = os.getenv("JLINK_TARGET")
        if jlink_target:
            matches = [m for m in matches if m.group(1) == jlink_target]
        if len(matches) == 0:
            raise GatewayError("Gateway not found")
        if len(matches) > 1:
            raise GatewayError("Too many candidates ("
                + ",".join([m.group(1) for m in matches]) + ")")
        self.serial = int(matches[0].group(1))
        self.dev = f"{dev_dir}/{matches[0].group(0)}"
        logger.debug("Selected port: " + os.path.realpath(self.dev))

    def read_fw_version(self):
        """ Reads firmware version of the device.
        """
        if self.serial is None or self.dev is None:
            raise GatewayError("Can not read fw version. Gateway not found")
        self.jlink.open(self.serial)
        self.jlink.set_tif(pylink.JLinkInterfaces.SWD)
        self.jlink.connect("nRF52832_xxAA")
        assert self.jlink.target_connected()
        self.fw_id, major, minor, fix = self.jlink.memory_read32(0x10001080, 4)
        self.jlink.close()
        self.version = version.parse(f"{major}.{minor}.{fix}")
        logger.debug("FW version: " + str(self.version))

    def flash(self):
        """ Downloads the lastest firmware from AWS S3 and flashes it to the
        device.
        """
        if self.serial is None:
            raise GatewayError("Can not flash firmware. Gateway not found")
        sd_file, fw_file = s3_helper.download_firmware(FW_VERSION, self.BOARD)
        self.jlink.open(self.serial)
        self.jlink.set_tif(pylink.JLinkInterfaces.SWD)
        self.jlink.connect("nRF52832_xxAA")
        assert self.jlink.target_connected()
        self.jlink.erase()
        self.jlink.flash_file(sd_file, None)
        self.jlink.flash_file(fw_file, None)
        self.jlink.reset(halt=False)
        self.jlink.close()

    def hard_reset(self):
        """ Hard resets the device.
        """
        if self.serial is None:
            raise GatewayError("Can not flash firmware. Gateway not found")
        self.jlink.open(self.serial)
        self.jlink.set_tif(pylink.JLinkInterfaces.SWD)
        self.jlink.connect("nRF52832_xxAA")
        assert self.jlink.target_connected()
        self.jlink.reset(halt=False)
        self.jlink.close()
        logger.debug("Hard reset device")

    def _supress_log(self, *args, **kwargs):
        pass
