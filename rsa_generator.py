from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class KeyGenerator:    
    def generate_keys(self):
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
    
    # Method to encode the private key with a PIN
    # This method uses Scrypt for key derivation and AES-GCM for encryption
    def encode_private_key(self, private_key, pin):
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