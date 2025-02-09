import logging

from ttgwlib import commands
from ttgwlib.events.event import EventType
from ttgwlib.provisioning.encryption import CryptoFormat as CF


NODE_START_UNICAST = 21


class Provisioner:
    def __init__(self, gateway):
        self.logger = logging.getLogger(__name__)
        self.gw = gateway
        self.node = None
        self.private_key = bytes()
        self.public_key = bytes()

    def obtain_unicast_addr(self):
        used_addr = {node.unicast_addr for node in self.gw.node_db.get_nodes()}
        max_addr = NODE_START_UNICAST + self.gw.dev_manager.cache_size
        for addr in range(NODE_START_UNICAST, max_addr):
            if addr not in used_addr:
                self.gw.dev_manager.clear_replay_cache(addr)
                return addr
        return None

    def set_key_pair(self):
        self.private_key, self.public_key = CF.obtain_new_keys()
        msg = commands.KeypairSet(CF.private_key_to_raw(self.private_key),
            CF.public_key_to_raw(self.public_key))
        self.gw.uart.send_msg(msg.serialize())

    def prov_start(self):
        self.logger.info("Provisioning device %s", self.node)

        uuid = self.node.uuid
        netkey = self.gw.node_db.get_netkey()
        netkey_index = 0
        unicast_address = self.node.unicast_addr
        msg = commands.Provision(uuid, netkey, netkey_index, unicast_address)

        self.gw.add_event_handler(self.prov_handler)
        self.gw.uart.send_msg(msg.serialize())

    def oob_use(self):
        # OOB not used
        msg = commands.OobUse(0, 0, 0)
        self.gw.uart.send_msg(msg.serialize())

    def ecdh_response(self, peer_public, private):
        peer_public_key = CF.raw_to_public_key(peer_public)
        private_key = CF.raw_to_private_key(private)
        shared_secret = CF.shared_secret(private_key, peer_public_key)

        msg = commands.EcdhSecret(shared_secret)
        self.gw.uart.send_msg(msg.serialize())

    def prov_complete(self, devkey):
        self.node.devkey = devkey
        self.gw.node_db.store_node(self.node)
        self.logger.info(f"Node {self.node.mac.hex()} provisioned "
            + "successfully")

    def prov_end(self, close_reason):
        self.gw.remove_event_handler(self.prov_handler)
        self.gw.prov_man.end_provision()
        self.node = None

    def prov_handler(self, event):
        if event.event_type == EventType.PROV_LINK_ESTABLISHED:
            self.logger.debug("Link established")

        elif event.event_type == EventType.PROV_LINK_CLOSED:
            self.logger.debug("Link closed: %d (%s)",
                    event.data["close_reason"], self.node.mac.hex())
            self.prov_end(event.data["close_reason"])

        elif event.event_type == EventType.PROV_CAPS:
            self.logger.debug("OOB capabilities received")
            self.oob_use()

        elif event.event_type == EventType.PROV_ECDH:
            self.logger.debug("ECDH request")
            self.ecdh_response(event.data["peer_public"], event.data["private"])

        elif event.event_type == EventType.PROV_COMPLETE:
            self.prov_complete(event.data["device_key"])

        elif event.event_type == EventType.PROV_FAILED:
            self.logger.warning("Provisioning failed: %d",
                event.data["error_code"])

    def provision(self, node):
        unicast_address = self.obtain_unicast_addr()
        if unicast_address is None:
            self.logger.error("There are no unicast addresses left")
            #TODO: Remove this limit
            return

        self.node = node
        self.node.unicast_addr = unicast_address
        self.gw.replay_cache.remove_node(self.node.unicast_addr)
        self.set_key_pair()
        self.prov_start()
