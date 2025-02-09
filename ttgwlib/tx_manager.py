import queue
import threading
import logging

from ttgwlib import commands
from ttgwlib.events.event import EventType


logger = logging.getLogger(__name__)


class TxManager:
    TTL = 127
    FORCE_SEGMENTED = False
    TRANSMIC_SIZE = 0

    def __init__(self, gateway):
        self.gw = gateway
        self.handles = self.gw.dev_manager.handles
        self.gw.add_event_handler(self.rsp_handler)
        self.gw.add_event_handler(self.sent_handler)

        # Size 10 already fails on a nRF52832. 5 works, 3 for safety
        self.semaphore = threading.Semaphore(3)
        self.pending = set()

        self.send_queue = queue.Queue()
        self.low_priority_queue = queue.Queue()
        self.running = True
        threading.Thread(target=self._run, name="TxManager").start()

    def rsp_handler(self, event):
        if event.event_type == EventType.RSP_SEND:
            if event.data["result"] == 0:
                self.pending.add(event.data["token"])
            else:
                logger.warning("SEND failed: %d", event.data["result"])
                self.semaphore.release()

    def sent_handler(self, event):
        if event.event_type == EventType.MESH_TX_COMPLETE:
            if event.data["token"] in self.pending:
                self.pending.remove(event.data["token"])
                self.semaphore.release()

    def send_node(self, data, node):
        if not self.gw.is_listener() and not self.gw.is_provisioner_mode():
            self.send_queue.put((data, node))

    def send_addr(self, data, addr, low_priority=False):
        if low_priority:
            self.low_priority_queue.put((data, addr))
        else:
            self.send_queue.put((data, addr))

    def _run(self):
        while self.running:
            try:
                data, dst = self.send_queue.get(timeout=0.1)
            except queue.Empty:
                try:
                    data, dst = self.low_priority_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

            while not self.semaphore.acquire(timeout=1):
                if not self.running:
                    break

            if isinstance(dst, int):
                self._send_addr(data, dst)
            else:
                self._send_node(data, dst)

    def _send_node(self, data, node):
        key_handle = self.handles.get_devkey_handle(node)
        addr_handle = self.handles.get_address_handle(node.unicast_addr)

        msg = commands.PacketSend(key_handle, self.gw.node_db.get_address(),
            addr_handle, self.TTL, self.FORCE_SEGMENTED, self.TRANSMIC_SIZE,
            data)
        self.gw.dev_manager.send_cmd_wait_rsp(msg)

    def _send_addr(self, data, addr):
        addr_handle = self.handles.get_address_handle(addr)

        msg = commands.PacketSend(self.handles.appkey,
            self.gw.node_db.get_address(), addr_handle, self.TTL,
            self.FORCE_SEGMENTED, self.TRANSMIC_SIZE, data)
        self.gw.dev_manager.send_cmd_wait_rsp(msg)

    def stop(self):
        self.running = False
