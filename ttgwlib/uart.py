"""
ttgwlib.uart
~~~~~~~~~~~~

Low level communication module. This module sends and receives packets
from the device via serial port.

"""
import time
import queue
import logging
import threading

import serial


class Uart:
    """ Class to communicate with a device through UART, using the
    PySerial library. By default, it uses a baud rate of 115200 and
    RTS/CTS flow control.

    The class initializes to threads, one for reading the port and
    another one for writing. The reading thread reads the bytes one at
    a time, and stores them in a queue. They can be get by the function
    :function:`get_byte`. To write, a bytearray object can be passed
    to the function :function:`send_msg`, which will store the message
    in another queue. The messages will be sent one at a time, in
    blocks of 40 bytes at maximun.

    :param logger: Logger.
    :type logger: :class:`logging.Logger`
    """
    def __init__(self, port):
        self.logger = logging.getLogger(__name__)
        self.serial = serial.Serial(port, baudrate=115200, rtscts=True,
            timeout=0.5)
        self.port = port
        self.read_running = False
        self.write_running = False
        self.connected = False
        time.sleep(0.1)
        self.start()

    def start(self):
        """ Starts the reading and writing threads. """
        self.read_running = True
        self.write_running = True
        self.connected = True
        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self.read_thd = threading.Thread(target=self.read, name='Reader')
        self.write_thd = threading.Thread(target=self.write, name='Writer')
        self.read_thd.start()
        self.write_thd.start()

    def stop(self):
        """ Stops the threads and closes the port. The reading thread
        is closed first. Then, all pending messages are wirtten and
        finally the port is closed.
        """
        self.read_running = False
        self.write_running = False
        self.connected = False

    def read(self):
        """ Read loop function, executed by the thread. """
        self.serial.reset_input_buffer()
        while self.read_running:
            msg = self.serial.read()
            if msg:
                self.read_queue.put(msg)

    def write(self):
        """ Write loop function, excuted by the thread. """
        while self.write_running:
            try:
                msg = self.write_queue.get(timeout=1)
                for i in range(0, len(msg), 40):
                    split = msg[i: i + 40]
                    self.serial.write(split)
            except queue.Empty:
                continue
        # When the write_thread is closed, wait for read_thread to end
        self.read_thd.join()
        # Then, send any messages left
        while not self.write_queue.empty():
            try:
                msg = self.write_queue.get(timeout=1)
                for i in range(0, len(msg), 40):
                    split = msg[i: i + 40]
                    self.serial.write(split)
            except queue.Empty:
                break
        self.serial.flush()
        self.serial.close()

    def get_byte(self, timeout=None):
        """ Returns read bytes in order, one at a time.

        :return: Read byte.
        :rtype: bytearray
        """
        try:
            return self.read_queue.get(timeout=timeout)
        except queue.Empty:
            return bytes()

    def send_msg(self, msg):
        """ Sends a message.

        :param msg: Message to be sent.
        :type msg: bytes or bytearray
        """
        self.logger.log(9, f"TX: {msg.hex()}")
        self.write_queue.put(msg)

    def is_connected(self):
        return self.connected

    def clean(self):
        self.read_queue.queue.clear()
