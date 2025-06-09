"""
Key generation and encryption module.

This module provides a class to generate RSA key pairs and encrypt the private key using
a password (PIN) with Scrypt key derivation and AES-GCM encryption.
"""

import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class KeyGenerator:
    """
    A class for generating and encrypting RSA key pairs.

    This class generates RSA private/public key pairs and securely encodes
    the private key using a PIN.
    """

    def generate_keys(self):
        """
        Generate an RSA private and public key pair.

        :return: A tuple containing the private key and public key in PEM format.
        :rtype: tuple(bytes, bytes)
        """
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=4096
        )

        private_key = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        )

        public_key = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_key, public_key

    def encode_private_key(self, private_key, pin):
        """
        Encrypt the private key using the provided PIN.

        Uses Scrypt for key derivation and AES-GCM for authenticated encryption.

        :param private_key: The private key to encrypt, in PEM format as bytes.
        :type private_key: bytes
        :param pin: The user's PIN used as the password for key derivation.
        :type pin: str
        :return: The encrypted private key with prepended salt and nonce.
        :rtype: bytes
        """
        salt = os.urandom(16)
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )

        key = kdf.derive(pin.encode())
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        encrypted_key = aesgcm.encrypt(nonce, private_key, None)

        return salt + nonce + encrypted_key
