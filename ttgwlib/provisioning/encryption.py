
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import \
    Encoding, PrivateFormat, PublicFormat, NoEncryption, \
    load_der_private_key, load_der_public_key

class CryptoFormat:
    public_der_format = bytearray()
    private_pkcs8_format = bytearray()

    @classmethod
    def obtain_new_keys(cls):
        private_key = ec.generate_private_key(ec.SECP256R1(),default_backend())
        public_key = private_key.public_key()
        return (private_key, public_key)

    @classmethod
    def shared_secret(cls, private_key, peer_public_key):
        return private_key.exchange(ec.ECDH(), peer_public_key)

    @classmethod
    def public_key_to_raw(cls, public_key):
        cls.public_der_format = public_key.public_bytes(Encoding.DER,
            PublicFormat.SubjectPublicKeyInfo)
        # Public key is the last 64 bytes of the formatted key.
        return cls.public_der_format[len(cls.public_der_format) - 64:]

    @classmethod
    def private_key_to_raw(cls, private_key):
        cls.private_pkcs8_format = private_key.private_bytes(Encoding.DER,
            PrivateFormat.PKCS8, NoEncryption())
        # Private key is found from byte 36 to 68 in the formatted key.
        return cls.private_pkcs8_format[36:68]

    @classmethod
    def raw_to_public_key(cls, public_bytes):
        key = cls.public_der_format[:-64]
        key += public_bytes
        public_key = load_der_public_key(key, default_backend())
        return public_key

    @classmethod
    def raw_to_private_key(cls, private_bytes):
        key = cls.private_pkcs8_format[:36]
        key += private_bytes
        key += cls.private_pkcs8_format[68:]
        private_key = load_der_private_key(key, None, default_backend())
        return private_key
