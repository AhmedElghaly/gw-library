
class ScanFilter:
    def __init__(self, uuid_filters=None, mac_filters=None):
        if uuid_filters is None:
            uuid_filters = []
        if mac_filters is None:
            mac_filters = []
        self.uuid_filters = uuid_filters
        self.mac_filters = mac_filters

    def uuid_filter(self, uuid, node):
        if uuid.lower() == node.uuid.hex()[0:len(uuid)].lower():
            return True
        return False

    def mac_filter(self, mac, node):
        if mac.lower() == node.mac.hex()[0:len(mac)].lower():
            return True
        return False

    def check(self, node):
        for uuid in self.uuid_filters:
            if self.uuid_filter(uuid, node):
                return True
        for mac in self.mac_filters:
            if self.mac_filter(mac, node):
                return True
        return False
