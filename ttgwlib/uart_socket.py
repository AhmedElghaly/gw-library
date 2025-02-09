import queue
import logging
import threading
import socket


logger = logging.getLogger(__name__)


class UartSocket:
    def __init__(self, _socket):
        self.socket = _socket
        self.socket.settimeout(20)
        self.read_running = False
        self.write_running = False
        self.connected = False
        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self.read_thd = threading.Thread(target=self.read, name='Reader')
        self.write_thd = threading.Thread(target=self.write, name='Writer')
        self.start()

    def start(self):
        self.read_running = True
        self.write_running = True
        self.connected = True
        self.read_thd.start()
        self.write_thd.start()

    def stop(self):
        self.read_running = False
        self.write_running = False
        self.connected = False

    def read(self):
        """ Read loop function, executed by the thread. """
        while self.read_running:
            try:
                msg = self.socket.recv(4096)
                if not msg:
                    logger.error("Receive error")
                    self.connected = False
                    break
                for b in msg:
                    self.read_queue.put(int.to_bytes(b, 1, "little"))
            except socket.timeout:
                continue

    def write(self):
        """ Write loop function, excuted by the thread. """
        while self.write_running:
            try:
                msg = self.write_queue.get(timeout=1)
                sent = self.socket.send(msg)
                if sent != len(msg):
                    logger.error(f"Send error: {sent}/{len(msg)}")
            except queue.Empty:
                continue

        # When the write_thread is closed, wait for read_thread to end
        self.read_thd.join()
        # Then, send any messages left
        while not self.write_queue.empty():
            msg = self.write_queue.get()
            self.socket.sendall(msg)
        self.socket.close()

    def get_byte(self, timeout=None):
        try:
            return self.read_queue.get(timeout=timeout)
        except queue.Empty:
            return bytes()

    def send_msg(self, msg):
        logger.log(9, f"TX: {msg.hex()}")
        self.write_queue.put(msg)

    def is_connected(self):
        return self.connected
