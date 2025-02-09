import logging
from enum import IntEnum, auto

from ttgwlib.platform.exception import GatewayError


logger = logging.getLogger(__name__)


class Platform(IntEnum):
    DESKTOP = auto()
    HEIMDALL_V1 = auto()
    HEIMDALL_V2 = auto()
    CM_V1 = auto()
    CLOUD = auto()

    @classmethod
    def from_string(cls, platform):
        if platform == "desktop":
            return cls.DESKTOP
        if platform in ("heimdall", "heimdall_v1"):
            return cls.HEIMDALL_V1
        if platform == "heimdall_v2":
            return cls.HEIMDALL_V2
        if platform == "cm_v1":
            return cls.CM_V1
        if platform == "cloud":
            return cls.CLOUD
        raise GatewayError("Invalid platform: " + str(platform))
