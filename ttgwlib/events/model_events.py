import struct

from ttgwlib.events.event import Event, EventType


class ModelEvent(Event):
    """ Class for model related events and communication.

    :param evt_type: Event Type.
    :type evt_type: :class: `events.event.EventType`
    :param data: Related event data.
    :type data: dict
    :param node: Node generating the event.
    :type node: :class:`~node.Node`

    Model msg parameters
    ----------
        src : uint16_t
            Source address of the received packet.
        dst : uint16_t
            Destination unicast address or subscription handle.
        appkey_handle : uint16_t
            Handle of the application the message was received on.
        subnet_handle : uint16_t
            Handle of the subnetwork the message was received on.
        ttl : uint8_t
            Packet time to live value when first received.
        adv_addr_type : uint8_t
            Advertisement address type of the last hop sender.
        adv_addr : uint8_t[6]
            Advertisement address of the last hop sender.
        rssi : int8_t
            RSSI value of the message when received.
        actual_length : uint16_t
            Length of the received message, may be larger than the data
            reported if SERIAL_EVT_MESH_MESSAGE_RECEIVED_DATA_MAXLEN
            is not big enough.
        sequence_number: uint32_t
            For relay cache
        data : uint8_t[78]
            Data payload of the packet.
    """
    def __init__(self, event_type, data, node, gw):
        super().__init__(event_type, data, gw)
        self.node = node


class UnknownNode(ModelEvent):
    def __init__(self, mesh_data, gw):
        data = {}
        data["mac"] = mesh_data["adv_addr"].hex()
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.UNKNOWN_NODE, data, None, gw)


class NodeReset(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        super().__init__(EventType.NODE_RESET, data, node, gw)


class TempData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<HB3sB", raw_data)
        data["temp"] = data_unpacked[0]
        data["hum"] =  data_unpacked[1]
        data["press"] = int.from_bytes(data_unpacked[2], "little")
        data["tid"] =  data_unpacked[3]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TEMP_DATA, data, node, gw)


class TempDataReliable(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<HB3sB", raw_data)
        data["temp"] = data_unpacked[0]
        data["hum"] =  data_unpacked[1]
        data["press"] = int.from_bytes(data_unpacked[2], "little")
        data["tid"] =  data_unpacked[3]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TEMP_DATA_RELIABLE, data, node, gw)


class IaAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.IA_ACK, data, node, gw)


class TempConfigAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TEMP_CONFIG_ACK, data, node, gw)


class TempCalibAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TEMP_CALIB_ACK, data, node, gw)


class TempCalResetAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TEMP_CALIB_RESET_ACK, data, node, gw)


class TempHeaterNotify(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TEMP_HEATER_NOTIFY, data, node, gw)


class IaqData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<BHBHB", raw_data)
        data["iaq"] = data_unpacked[0]
        data["tvoc"] = data_unpacked[1]
        data["etoh"] = data_unpacked[2]
        data["eco2"] = data_unpacked[3]
        data["tid"] = data_unpacked[4]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.IAQ_DATA, data, node, gw)


class Co2Data(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<HBHB", raw_data)
        data["co2"] = data_unpacked[0]
        data["cal_status"] = data_unpacked[1]
        data["abc_time"] = data_unpacked[2]
        data["tid"] = data_unpacked[3]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.CO2_DATA, data, node, gw)


class PwmtData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data[:1])
        data["ctl"] = data_unpacked[0]
        phase_id = data["ctl"] & 0b11
        message_id = (data["ctl"] >> 2) & 0b11
        # value_type = (data["ctl"] >> 4) & 0b11
        # calc_status = (data["ctl"] >> 6) & 0b11
        if phase_id == 0:
            if message_id == 0:
                data_unpacked = struct.unpack("<Bhhh", raw_data)
                data["p_tot"] = data_unpacked[1]
                data["q_tot"] = data_unpacked[2]
                data["s_tot"] = data_unpacked[3]
            elif message_id == 1:
                data_unpacked = struct.unpack("<Bhhh", raw_data)
                data["ph12"] = data_unpacked[1] / 100
                data["ph23"] = data_unpacked[2] / 100
                data["ph31"] = data_unpacked[3] / 100
            elif message_id == 2:
                data_unpacked = struct.unpack("<BHHH", raw_data)
                data["v12"] = data_unpacked[1] / 100
                data["v23"] = data_unpacked[2] / 100
                data["v31"] = data_unpacked[3] / 100
            elif message_id == 3:
                data_unpacked = struct.unpack("<Bi", raw_data[:-2])
                data["e_tot"] = data_unpacked[1]
        else:
            if message_id == 0:
                data_unpacked = struct.unpack("<BHHH", raw_data)
                data["v"] = data_unpacked[1] / 100
                data["i"] = data_unpacked[2] / 100
                data["f"] = data_unpacked[3] / 100
            elif message_id == 1:
                data_unpacked = struct.unpack("<Bhh", raw_data[:-2])
                data["p"] = data_unpacked[1]
                data["pf"] = (data_unpacked[2] & 0x7F) / 100
                data["ind"] = data_unpacked[2] >> 16 & 1
            elif message_id == 2:
                data_unpacked = struct.unpack("<Bhhh", raw_data)
                data["q"] = data_unpacked[1]
                data["s"] = data_unpacked[2]
                data["ph"] = data_unpacked[3] / 100
            elif message_id == 3:
                data_unpacked = struct.unpack("<Bi", raw_data[:-2])
                data["e"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.PWMT_DATA, data, node, gw)


class PwmtConfigAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.PWMT_CONFIG_ACK, data, node, gw)


class PwmtConvAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.PWMT_CONV_ACK, data, node, gw)


class OutputDacAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.OUTPUT_DAC_ACK, data, node, gw)


class OutputDigAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.OUTPUT_DIG_ACK, data, node, gw)


class BatData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<HB", raw_data)
        data["bat"] = data_unpacked[0]
        data["tid"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.BAT_DATA, data, node, gw)


class LightAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.LIGHT_ACK, data, node, gw)


class TapNotify(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<BBB", raw_data)
        data["type"] = data_unpacked[0]
        data["color"] = data_unpacked[1]
        data["tid"] = data_unpacked[2]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TAP_NOTIFY, data, node, gw)


class TapAckConf(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TAP_ACK_CONF, data, node, gw)


class RssiNeighbrAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.RSSI_NEIGHBR_ACK, data, node, gw)


class RssiNeighbrData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<Hb", raw_data)
        data["addr"] = data_unpacked[0]
        data["rssi"] = data_unpacked[1]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.RSSI_NEIGHBR_DATA, data, node, gw)


class RssiStatusAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<b", raw_data)
        data["rssi"] = data_unpacked[0]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.RSSI_STATUS_ACK, data, node, gw)


class RssiPing(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.RSSI_PING, data, node, gw)


class RssiPingAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.RSSI_PING_ACK, data, node, gw)


class PowerAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.POWER_ACK, data, node, gw)


class HwmData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<BBBB", raw_data)
        data["hts"] = data_unpacked[0]
        data["sht"] = data_unpacked[1]
        data["fxx"] = data_unpacked[2]
        data["lps"] = data_unpacked[3]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.HWM_DATA, data, node, gw)

class HwmAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.HWM_ACK, data, node, gw)


class DatetimeReq(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["tid"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.DATETIME_REQ, data, node, gw)


class DatetimeAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.DATETIME_ACK, data, node, gw)


class TaskAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<bB", raw_data)
        data["task_index"] = data_unpacked[0]
        data["tid"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TASK_ACK, data, node, gw)


class TaskChangeAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<bB", raw_data)
        data["task_index"] = data_unpacked[0]
        data["tid"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TASK_CHANGE_ACK, data, node, gw)


class TaskDeleteAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<bB", raw_data)
        data["delete_code"] = data_unpacked[0]
        data["tid"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TASK_DELETE_ACK, data, node, gw)


class TaskDeleteOpAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<bB", raw_data)
        data["delete_code"] = data_unpacked[0]
        data["tid"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TASK_DELETE_OP_ACK, data, node, gw)


class TaskData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<BI3s", raw_data)
        data["opcode"] = data_unpacked[0]
        data["event_date"] = data_unpacked[1]
        data["period"] = int.from_bytes(data_unpacked[2], "little")
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TASK_SEND_TASKS, data, node, gw)


class TaskGetTasksAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TASK_GET_TASKS_ACK, data, node, gw)


class WakeNotify(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        if len(raw_data) == 2:
            data_unpacked = struct.unpack("<BB", raw_data)
            data["tid"] = data_unpacked[0]
            data["conf"] = bool(data_unpacked[1])
        else:
            data_unpacked = struct.unpack("<B", raw_data)
            data["tid"] = data_unpacked[0]
        super().__init__(EventType.WAKE_NOTIFY, data, node, gw)


class WakeReset(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<BB", raw_data)
        data["board_id"] = data_unpacked[0]
        data["reset_reason"] = data_unpacked[1]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.WAKE_RESET, data, node, gw)


class WakeAckSleep(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.WAKE_ACK_SLEEP, data, node, gw)


class WakeAckWait(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.WAKE_ACK_WAIT, data, node, gw)


class WakeAckAlive(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.WAKE_ACK_ALIVE, data, node, gw)


class OtaVersionAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["status"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.OTA_VERSION_ACK, data, node, gw)


class OtaStatusAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["status"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.OTA_STATUS_ACK, data, node, gw)

class OtaStoreAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["status"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.OTA_STORE_ACK, data, node, gw)

class OtaRelayAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["status"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.OTA_RELAY_ACK, data, node, gw)

class BeaconStartAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["tid"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.BEACON_START_ACK, data, node, gw)


class BeaconStopAck(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<B", raw_data)
        data["tid"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.BEACON_STOP_ACK, data, node, gw)

class TransportRecv(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["data"] = raw_data
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TRANSPORT_RECV, data, node, gw)

class TransportFrStart(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<H", raw_data)
        data["len"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TRANSPORT_FR_START, data, node, gw)

class TransportFrEnd(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data_unpacked = struct.unpack("<6p",raw_data)
        data["sum"] = data_unpacked[0]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TRANSPORT_FR_END, data, node, gw)

class TransportFrData(ModelEvent):
    def __init__(self, mesh_data, raw_data, node, gw):
        data = {}
        data["seq"], = struct.unpack("<H", raw_data[0:2])
        data["data"] = raw_data[2:]
        data["rssi"] = mesh_data["rssi"]
        data["ttl"] = mesh_data["ttl"]
        data["src"] = mesh_data["src"]
        data["sequence_number"] = mesh_data["sequence_number"]
        super().__init__(EventType.TRANSPORT_FR_DATA, data, node, gw)
