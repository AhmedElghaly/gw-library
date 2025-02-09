import logging
import ssl
import socket
import time
import threading

from ttgwlib import commands


logger = logging.getLogger(__name__)


class Passthrough:
    def __init__(self, host, port, uart, programmer):
        self.host = host
        self.port = port
        self.uart = uart
        self.programmer = programmer
        self.socket = None
        self.connected = False
        self.ssl_context = None
        self.rx_thd = None
        self.tx_thd = None
        self.socket_thd = threading.Thread(target=self.keep_connected)
        self.running = False
        self.timeout = 10

    def create_default_ssl_context(self):
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.options |= ssl.OP_NO_SSLv2
        self.ssl_context.options |= ssl.OP_NO_SSLv3
        self.ssl_context.options |= ssl.OP_NO_TLSv1
        self.ssl_context.options |= ssl.OP_NO_TLSv1_1
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def set_ca_cert(self, ca_cert):
        if self.ssl_context is None:
            self.create_default_ssl_context()
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        self.ssl_context.load_verify_locations(ca_cert)

    def set_client_auth(self, client_cert, client_key):
        if self.ssl_context is None:
            self.create_default_ssl_context()
        self.ssl_context.load_cert_chain(client_cert, client_key)

    def relay_rx(self):
# pylint: disable=broad-exception-caught
        try:
            while self.running and self.connected:
                msg = bytearray()
                while len(msg) < 255:
                    b = self.uart.get_byte(0.01)
                    if b:
                        msg += b
                    else:
                        break
                if msg:
                    try:
                        self.socket.sendall(msg)
                    except socket.error:
                        self.connected = False
                        break
        except Exception as exc:
            logger.error(exc)
# pylint: disable=broad-exception-caught

    def relay_tx(self):
        while self.running and self.connected:
            try:
                msg = self.socket.recv(4096)
                if not msg:
                    self.connected = False
                    break
                self.uart.send_msg(msg)
            except socket.timeout:
                continue
            except socket.error:
                self.connected = False
                break

    def keep_connected(self):
        while self.running:
            try:
                self.rx_thd = threading.Thread(target=self.relay_rx)
                self.tx_thd = threading.Thread(target=self.relay_tx)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)
                if self.ssl_context:
                    self.socket = self.ssl_context.wrap_socket(self.socket)
                logger.debug(f"Trying to connect to {self.host}:{self.port}")
                self.socket.connect((self.host, self.port))
                logger.debug("Connected")
                self.connected = True
            except socket.error:
                logger.debug("Unable to connect. " + \
                    f"Retrying in {self.timeout} sec")
                self.socket.close()
                time.sleep(self.timeout)
                continue
            self.uart.clean()
            self.rx_thd.start()
            self.tx_thd.start()
            if self.programmer:
                self.programmer.hard_reset()
            else:
                msg = commands.Reset()
                self.uart.send_msg(msg.serialize())
            while self.connected:
                time.sleep(1)
            logger.debug("Connection closed")
            if self.rx_thd.is_alive():
                self.rx_thd.join()
            if self.tx_thd.is_alive():
                self.tx_thd.join()
            self.socket.close()

    def stop(self):
        logger.debug("Stopping passthrough mode")
        self.running = False
        self.socket.close()
        if self.rx_thd.is_alive():
            self.rx_thd.join()
        if self.tx_thd.is_alive():
            self.tx_thd.join()
        if self.socket_thd.is_alive():
            self.socket_thd.join()
        if self.uart:
            self.uart.stop()

    def start(self):
        logger.debug("Starting passthrough mode")
        self.running = True
        self.socket_thd.start()

    def is_connected(self):
        logger.debug(f"Passthrough is connected: {self.connected}")
        return self.connected
