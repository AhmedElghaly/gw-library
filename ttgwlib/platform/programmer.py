
class Programmer:
    """ This abstract class shows the programmer interface.

    It should be inherited by any user implementation of the programmer.
    """
    def get_fw_version(self):
        """ Returns the firmware version.

        :return: Firmware version.
        :rtype: str
        """
        raise NotImplementedError

    def get_serial_port(self):
        """ Returns the serial port.

        :return: Serial port.
        :rtype: str
        """
        raise NotImplementedError

    def init(self):
        """ Connects to the device and reads the lastest version.
        Returns the path to the serial interface.

        :return: Path of the serial interface.
        :rtype: str
        """
        raise NotImplementedError

    def update_fw(self):
        """ Updates the firmware of the device to the lastest version.
        """
        raise NotImplementedError

    def hard_reset(self):
        """ Hard resets the device.
        """
        raise NotImplementedError
