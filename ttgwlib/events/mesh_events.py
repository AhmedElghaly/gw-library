import struct

from ttgwlib.events.event import Event, EventType


class DeviceStarted(Event):
    """ The device has started, and is ready for commands.

    Parameters
    ----------
        operating_mode : uint8_t
            Operating mode of the device. See serial_device_operating_mode_t for
            accepted values.
        hw_error : uint8_t
            Hardware error code, or 0 if no error occured.
        data_credit_available : uint8_t
            The number of bytes available in each of the tx and rx buffers.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<BBB", raw_data)
        data = {}
        data["operating_mode"] = data_unpacked[0]
        data["hw_error"] = data_unpacked[1]
        data["data_credit_available"] = data_unpacked[2]
        super().__init__(EventType.DEV_RESET, data, gw)


class EchoRsp(Event):
    """ Echo event. Return the same data previously sent. """
    def __init__(self, raw_data, gw):
        data = {}
        data["echo"] = raw_data
        super().__init__(EventType.ECHO, data, gw)


class ProvUnprovisionedReceived(Event):
    """ The node received an unprovisioned beacon.

    Parameters
    ----------
        uuid : uint8_t[16]
            UUID in the unprovisioned beacon.
        rssi : int8_t
            RSSI of the received unprovisioned beacon.
        gatt_supported : uint8_t
            Whether the unprovisioned device supports GATT provisioning.
        adv_addr_type : uint8_t
            The advertisement address type of the sender of the unprovisioned
            beacon.
        adv_addr : uint8_t[6]
            The advertisement address of the sender of the unprovisioned beacon.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<16sbBB6s", raw_data)
        data = {}
        data["uuid"] = data_unpacked[0]
        data["rssi"] = data_unpacked[1]
        data["gatt_supported"] = data_unpacked[2]
        data["adv_addr_type"] = data_unpacked[3]
        adv_addr = bytearray(data_unpacked[4])
        adv_addr.reverse()
        data["adv_addr"] = bytes(adv_addr)
        super().__init__(EventType.UNPROV_DISC, data, gw)


class ProvLinkEstablished(Event):
    """ The given provisioning link has been established.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the established link.
    """
    def __init__(self, raw_data, gw):
        #data_unpacked = struct.unpack("<B", raw_data)
        super().__init__(EventType.PROV_LINK_ESTABLISHED, {}, gw)


class ProvLinkClosed(Event):
    """ The given provisioning link has been closed.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the closed link.
        close_reason : uint8_t
            Reason for closing the link.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<BB", raw_data)
        data = {}
        data["close_reason"] = data_unpacked[1]
        super().__init__(EventType.PROV_LINK_CLOSED, data, gw)


class ProvCapsReceived(Event):
    """ The device received provisioning capabilities on the provisioning link
    with the given context ID.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the link the capabilities were received on.
        num_elements : uint8_t
            The number of elements on the unprovisoined device.
        public_key_type : uint8_t
            The public key type used for the provisioning session.
        static_oob_types : uint8_t
            The available static OOB authentication methods.
        output_oob_size : uint8_t
            Maximum size of the output OOB supported.
        output_oob_actions : uint16_t
            Available OOB output actions.
        input_oob_size : uint8_t
            Maximum size of the input OOB supported.
        input_oob_actions : uint16_t
            Available OOB input actions.
    """
    def __init__(self, raw_data, gw):
        #data_unpacked = struct.unpack("<BBBBBHBH", raw_data)
        super().__init__(EventType.PROV_CAPS, {}, gw)


class ProvComplete(Event):
    """ The provisioning process was successfully completed.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the completed provisioning link.
        iv_index : uint32_t
            IV index for the network.
        net_key_index : uint16_t
            Network key index.
        address : uint16_t
            Unicast address for the device.
        iv_update_flag : uint8_t
            IV update in progress flag.
        key_refresh_flag : uint8_t
            Key refresh in progress flag.
        device_key : uint8_t[16]
            The device key of the provisioned device.
        net_key : uint8_t[16]
            The network key of the provisioned device.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<BIHHBB16s16s", raw_data)
        data = {}
        data["device_key"] = data_unpacked[6]
        super().__init__(EventType.PROV_COMPLETE, data, gw)


class ProvAuthRequest(Event):
    """Static authentication data is required to continue.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the link the authorization request appeared on.
        method : uint8_t
            Method of authentication requested.
        action : uint8_t
            Authentication action.
        size : uint8_t
            Authentication size.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<BBBB", raw_data)
        data = {}
        data["method"] = data_unpacked[1]
        data["action"] = data_unpacked[2]
        data["size"] = data_unpacked[3]
        super().__init__(EventType.PROV_AUTH, data, gw)


class ProvEcdhRequest(Event):
    """ An ECDH shared secret must be calculated.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the link the ECDH request appeared on.
        peer_public : uint8_t[64]
            ECDH public key.
        private : uint8_t[32]
            ECDH private key.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<B64s32s", raw_data)
        data = {}
        data["peer_public"] = data_unpacked[1]
        data["private"] = data_unpacked[2]
        super().__init__(EventType.PROV_ECDH, data, gw)


class ProvFailed(Event):
    """The provisioning procedure failed.

    Parameters
    ----------
        context_id : uint8_t
            Context ID of the link the error happened on.
        error_code : uint8_t
            Provisioning error code.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<BB", raw_data)
        data = {}
        data["error_code"] = data_unpacked[1]
        super().__init__(EventType.PROV_FAILED, data, gw)


class MeshTxComplete(Event):
    def __init__(self, raw_data, gw):
        data = {}
        data["token"], = struct.unpack("<I", raw_data)
        super().__init__(EventType.MESH_TX_COMPLETE, data, gw)


class Application(Event):
    """Application event, only sent by the device application.

    Parameters
    ----------
        data : uint8_t[97]
            Application data.
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<B", raw_data[0:1])
        data = {}
        opcode = data_unpacked[0]

        if opcode == 0x02:
            data["seq_number"], = struct.unpack("<I", raw_data[1:])
            super().__init__(EventType.SEQ_UPDATE, data, gw)

        elif opcode == 0x04:
            data["cache_size"], = struct.unpack("<H", raw_data[1:])
            super().__init__(EventType.CACHE_SIZE, data, gw)

        elif opcode == 0x05:
            super().__init__(EventType.SD_ENABLED, data, gw)

        else:
            data = raw_data[0:]
            super().__init__(EventType.APP_EVENT, data, gw)


class CmdResponse(Event):
    """
    Response status values:

    SERIAL_STATUS_SUCCESS                   0x00
    SERIAL_STATUS_ERROR_UNKNOWN             0x80
    SERIAL_STATUS_ERROR_INTERNAL            0x81
    SERIAL_STATUS_ERROR_CMD_UNKNOWN         0x82
    SERIAL_STATUS_ERROR_INVALID_STATE       0x83
    SERIAL_STATUS_ERROR_INVALID_LENGTH      0x84
    SERIAL_STATUS_ERROR_INVALID_PARAMETER   0x85
    SERIAL_STATUS_ERROR_BUSY                0x86
    SERIAL_STATUS_ERROR_INVALID_DATA        0x87
    SERIAL_STATUS_ERROR_REJECTED            0x8e
    SERIAL_STATUS_ERROR_TIMEOUT             0x93
    SERIAL_STATUS_ERROR_INVALID_KEY_DATA    0x98
    """
    def __init__(self, raw_data, gw):
        data_unpacked = struct.unpack("<BB", raw_data[0:2])
        opcode = data_unpacked[0]
        result = data_unpacked[1]
        rsp_data = raw_data[2:]
        data = {}

        if opcode == 0xab:
            data["result"] = result
            if result == 0:
                data["token"], = struct.unpack("<I", rsp_data)
            else:
                data["token"] = -1
            super().__init__(EventType.RSP_SEND, data, gw)
        else:
            data["opcode"] = opcode
            data["result"] = result
            data["rsp_data"] = rsp_data
            super().__init__(EventType.RSP_EVENT, data, gw)
