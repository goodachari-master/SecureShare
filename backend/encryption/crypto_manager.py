from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import os
import base64
from config import config

class CryptoManager:
    @staticmethod
    def generate_aes_key():
        """Generate random AES-256 key"""
        return os.urandom(config.AES_KEY_SIZE)
    
    @staticmethod
    def generate_iv():
        """Generate random IV for AES-GCM"""
        return os.urandom(config.IV_SIZE)
    
    @staticmethod
    def encrypt_aes_gcm(plaintext, key, iv):
        """Encrypt data using AES-256-GCM"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return ciphertext, encryptor.tag
    
    @staticmethod
    def decrypt_aes_gcm(ciphertext, key, iv, tag):
        """Decrypt data using AES-256-GCM"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    @staticmethod
    def encrypt_rsa_oaep(data, public_key_pem):
        """Encrypt data using RSA-OAEP"""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted
    
    @staticmethod
    def decrypt_rsa_oaep(encrypted_data, private_key_pem):
        """Decrypt data using RSA-OAEP"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
    
    @staticmethod
    def encode_base64(data):
        """Encode bytes to base64 string"""
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def decode_base64(data_str):
        """Decode base64 string to bytes"""
        return base64.b64decode(data_str.encode('utf-8'))