import logging

from ttgwlib.models.model import Model


class Battery(Model):
    MODEL_ID = 0x0004
    VENDOR_ID = MODEL_ID
    DEFAULT_BATTERY_PERIOD = 86400 # 24 h

    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        super().__init__(gateway, [])
