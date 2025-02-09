from ttgwlib.events.event import Event, EventType


class UartDisconnection(Event):
    """ The device has started, and is ready for commands.
    """
    def __init__(self, gw):
        super().__init__(EventType.UART_DISCONNECTION, {}, gw)
