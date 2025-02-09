
import struct

class CommandPacket:
    def __init__(self, opcode, data):
        self._opcode = opcode
        self._data = data

    def __len__(self):
        return len(self._data) + 1

    def get_opcode(self):
        return self._opcode

    def serialize(self):
        return bytearray([len(self), self._opcode]) + self._data


class Echo(CommandPacket):
    """Echo command."""
    OPCODE = 0x02

    def __init__(self, msg):
        __data = bytearray()
        __data += msg
        super().__init__(self.OPCODE, __data)


class Reset(CommandPacket):
    """Restart the device."""
    OPCODE = 0x0E

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class AdvertisingAddressGet(CommandPacket):
    """Get the advertising address (Bluetooth mac)."""
    OPCODE = 0x41

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class StateClear(CommandPacket):
    """Reset the device and network state and erase the flash copies."""
    OPCODE = 0xAC

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class SetNetState(CommandPacket):
    """Set net state."""
    OPCODE = 0xAE

    def __init__(self, iv_index, iv_update, iv_update_timeout, sequence_number):
        __data = bytearray()
        __data += struct.pack("<IBHI", iv_index, iv_update, iv_update_timeout,
            sequence_number)
        super().__init__(self.OPCODE, __data)


class GetNetState(CommandPacket):
    """Get net state."""
    OPCODE = 0xAF

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class EnableMesh(CommandPacket):
    OPCODE = 0x90

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class DisableMesh(CommandPacket):
    OPCODE = 0x91

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class AddrLocalUnicastSet(CommandPacket):
    """Set the start and count of the device's local unicast address.

    Parameters
    ----------
        start_address : uint16_t
            First address in the range of unicast addresses.
        count : uint16_t
            Number of addresses in the range of unicast addresses.
    """
    OPCODE = 0x9F

    def __init__(self, start_address, count):
        __data = bytearray()
        __data += struct.pack("<H", start_address)
        __data += struct.pack("<H", count)
        super().__init__(self.OPCODE, __data)


class AddrLocalUnicastGet(CommandPacket):
    """Get the start and count of the device's local unicast addresses."""
    OPCODE = 0xA0

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class SubnetAdd(CommandPacket):
    """Add a mesh subnetwork to the device.

    Parameters
    ----------
        net_key_index : uint16_t
            Mesh-global key index.
        key : uint8_t[16]
            Key to add.
    """
    OPCODE = 0x92

    def __init__(self, net_key_index, key):
        __data = bytearray()
        __data += struct.pack("<H", net_key_index)
        __data += key
        super().__init__(self.OPCODE, __data)


class AppkeyAdd(CommandPacket):
    """Add a mesh application key to the device.

    Parameters
    ----------
        app_key_index : uint16_t
            Mesh-global key index.
        subnet_handle : uint16_t
            Handle of the subnetwork to add the appkey to.
        key : uint8_t[16]
            Key to add.
    """
    OPCODE = 0x97

    def __init__(self, app_key_index, subnet_handle, key):
        __data = bytearray()
        __data += struct.pack("<H", app_key_index)
        __data += struct.pack("<H", subnet_handle)
        __data += key
        super().__init__(self.OPCODE, __data)


class DevkeyAdd(CommandPacket):
    """Add a mesh device key to the device.

    Parameters
    ----------
        owner_addr : uint16_t
            Unicast address of the device that owns the given devkey.
        subnet_handle : uint16_t
            Handle of the subnetwork to bind the devkey to.
        key : uint8_t[16]
            Key to add.
    """
    OPCODE = 0x9C

    def __init__(self, owner_addr, subnet_handle, key):
        __data = bytearray()
        __data += struct.pack("<H", owner_addr)
        __data += struct.pack("<H", subnet_handle)
        __data += key
        super().__init__(self.OPCODE, __data)


class DevkeyDelete(CommandPacket):
    """Delete a device key from the device.

    Parameters
    ----------
        devkey_handle : uint16_t
            Handle of the devkey to delete.
    """
    OPCODE = 0x9D

    def __init__(self, devkey_handle):
        __data = bytearray()
        __data += struct.pack("<H", devkey_handle)
        super().__init__(self.OPCODE, __data)


class ScanStart(CommandPacket):
    """Start reporting of incoming unprovisioned beacons."""
    OPCODE = 0x61

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class ScanStop(CommandPacket):
    """Stop reporting of incoming unprovisioned beacons."""
    OPCODE = 0x62

    def __init__(self):
        __data = bytearray()
        super().__init__(self.OPCODE, __data)


class Provision(CommandPacket):
    """Start provisioning of a device.

    Parameters
    ----------
        context_id : uint8_t
            Context ID to use for this provisioning session.
        target_uuid : bytearray[16]
            UUID of the device to provision.
        network_key : bytearray[16]
            Network key to give to the device.
        network_key_index : uint16_t
            Network key index.
        iv_index : uint32_t
            Initial IV index of the network.
        address : uint16_t
            Unicast address to assign to the device.
        iv_update_flag : uint8_t
            IV update in progress flag.
        key_refresh_flag : uint8_t
            Key refresh in progress flag.
        attention_duration_s : uint8_t
            Time in seconds during which the device will identify
            itself using any means it can.
    """
    OPCODE = 0x63

    def __init__(self, target_uuid, network_key, network_key_index, address):
        __data = bytearray()
        __data += struct.pack("<B", 0) # context_id
        __data += target_uuid
        __data += network_key
        __data += struct.pack("<H", network_key_index)
        __data += struct.pack("<I", 0) # iv_index
        __data += struct.pack("<H", address)
        __data += struct.pack("<B", 0) # iv_update_flag
        __data += struct.pack("<B", 0) # key_refresh_flag
        __data += struct.pack("<B", 0) # attention_duration_s
        super().__init__(self.OPCODE, __data)


class OobUse(CommandPacket):
    """Used to respond to the _Provisioning Capabilities Received_ event.

    Parameters
    ----------
        context_id : uint8_t
            ID of context to set the oob method for.
        oob_method : uint8_t
            OOB method to use, see @ref nrf_mesh_prov_oob_method_t for accepted
            values. (Static oob: 0x01)
        oob_action : uint8_t
            OOB action to use, see @ref nrf_mesh_prov_input_action_t or @ref
            nrf_mesh_prov_output_action_t for values.
        size : uint8_t
            Size of the OOB data.
    """
    OPCODE = 0x66

    def __init__(self, oob_method, oob_action, size):
        __data = bytearray()
        __data += struct.pack("<B", 0) # context_id
        __data += struct.pack("<B", oob_method)
        __data += struct.pack("<B", oob_action)
        __data += struct.pack("<B", size)
        super().__init__(self.OPCODE, __data)


class AuthData(CommandPacket):
    """Used to respond to a _Provisioning Auth Request_ event.

    Parameters
    ----------
        context_id : uint8_t
            ID of the context to set the authentication data for.
        data : uint8_t[16]
            Authentication data.
    """
    OPCODE = 0x67

    def __init__(self, data):
        __data = bytearray()
        __data += struct.pack("<B", 0) # context_id
        __data += data
        super().__init__(self.OPCODE, __data)


class EcdhSecret(CommandPacket):
    """Used to respond to a _Provisioning ECDH Request_ event.

    Parameters
    ----------
        context_id : uint8_t
            ID of the context to set the shared secret for.
        shared_secret : uint8_t[32]
            ECDH shared secret.
    """
    OPCODE = 0x68

    def __init__(self, shared_secret):
        __data = bytearray()
        __data += struct.pack("<B", 0) # context_id
        __data += shared_secret
        super().__init__(self.OPCODE, __data)


class KeypairSet(CommandPacket):
    """Send a public/private keypair to the device.

    Parameters
    ----------
        private_key : uint8_t[32]
            Private key.
        public_key : uint8_t[64]
            Public key.
    """
    OPCODE = 0x69

    def __init__(self, private_key, public_key):
        __data = bytearray()
        __data += private_key
        __data += public_key
        super().__init__(self.OPCODE, __data)


class AddrSubscriptionAdd(CommandPacket):
    """Add the specified address to the set of active address subscriptions.

    Parameters
    ----------
        address : uint16_t
            Address to add as a subscription address.
    """
    OPCODE = 0xA1

    def __init__(self, address):
        __data = bytearray()
        __data += struct.pack("<H", address)
        super().__init__(self.OPCODE, __data)


class AddrSubscriptionRemove(CommandPacket):
    """Remove the address with the given handle from the set of active address
    subscriptions.

    Parameters
    ----------
        address_handle : uint16_t
            Handle of address to remove from address subscription list.
    """
    OPCODE = 0xA3

    def __init__(self, address_handle):
        __data = bytearray()
        __data += struct.pack("<H", address_handle)
        super().__init__(self.OPCODE, __data)


class AddrPublicationAdd(CommandPacket):
    """Add the specified address to the set of active publish addresses.

    Parameters
    ----------
        address : uint16_t
            Address to add as a publication address.
    """
    OPCODE = 0xA4

    def __init__(self, address):
        __data = bytearray()
        __data += struct.pack("<H", address)
        super().__init__(self.OPCODE, __data)


class AddrPublicationRemove(CommandPacket):
    """Remove the address with the specified handle from the set of active
    publish addresses.

    Parameters
    ----------
        address_handle : uint16_t
            Handle of the address to remove from the publication address list.
    """
    OPCODE = 0xA6

    def __init__(self, address_handle):
        __data = bytearray()
        __data += struct.pack("<H", address_handle)
        super().__init__(self.OPCODE, __data)


class PacketSend(CommandPacket):
    """Send a mesh packet.

    Parameters
    ----------
        appkey_handle : uint16_t
            Appkey or devkey handle to use for packet sending. Subnetwork will
            be picked automatically.
        src_addr : uint16_t
            Raw unicast address to use as source address. Must be in the range
            of local unicast addresses.
        dst_addr_handle : uint16_t
            Handle of destination address to use in packet.
        ttl : uint8_t
            Time To Live value to use in packet.
        force_segmented : uint8_t
            Whether or not to force use of segmented message type for the
            transmission.
        transmic_size : uint8_t
            Transport MIC size used enum. SMALL=0, LARGE=1, DEFAULT=2. LARGE may
            only be used with segmented packets.
        friendship_credential_flag : uint8_t
            Control parameter for credentials used to publish messages from a
            model. 0 for master, 1 for friendship.
        data : uint8_t[88]
            Payload of the packet.
    """
    OPCODE = 0xAB

    def __init__(self, appkey_handle, src_addr, dst_addr_handle, ttl,
            force_segmented, transmic_size, data):
        __data = bytearray()
        __data += struct.pack("<H", appkey_handle)
        __data += struct.pack("<H", src_addr)
        __data += struct.pack("<H", dst_addr_handle)
        __data += struct.pack("<B", ttl)
        __data += struct.pack("<B", force_segmented)
        __data += struct.pack("<B", transmic_size)
        __data += struct.pack("<B", 0) # friendship_credential_flag
        __data += data
        super().__init__(self.OPCODE, __data)


class Application(CommandPacket):
    """Application specific command, has no functionality in the framework, but
    is forwarded to the application.

    Parameters
    ----------
        opcode : uint8_t
            Operation code.
        data : uint8_t[97]
            Application data.
    """
    OPCODE = 0x20

    def __init__(self, opcode, data):
        __data = bytearray()
        __data += struct.pack("<B", opcode)
        if data is not None:
            __data += data
        super().__init__(self.OPCODE, __data)

class ClearNodeReplayCache(Application):
    def __init__(self, unicast_address):
        super().__init__(0x01, struct.pack("<H", unicast_address))

class GetReplayCacheSize(Application):
    def __init__(self):
        super().__init__(0x04, None)

class EnableSoftdevice(Application):
    def __init__(self):
        super().__init__(0x05, None)

class DisableSoftdevice(Application):
    def __init__(self):
        super().__init__(0x06, None)

class UpdateStartData(Application):
    def __init__(self, start_address, size, signature):
        data = struct.pack("<II", start_address, size)
        data += signature
        super().__init__(0x07, data)

class UpdateBinData(Application):
    def __init__(self, address, bin_data):
        data = struct.pack("<I", address)
        data += bin_data
        super().__init__(0x08, data)

class UpdateSend(Application):
    def __init__(self):
        super().__init__(0x09, None)

class SetLed(Application):
    def __init__(self, r, g, b):
        data = struct.pack("<BBB", r, g, b)
        super().__init__(0x0A, data)

class UpdateInstall(Application):
    def __init__(self, update_type):
        data = struct.pack("<I", update_type)
        super().__init__(0x0B, data)

class UpdateStatus(Application):
    def __init__(self):
        super().__init__(0x0C, None)
