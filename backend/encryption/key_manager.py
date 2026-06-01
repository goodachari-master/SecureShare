from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
from config import config
from .crypto_manager import CryptoManager

class KeyManager:
    @staticmethod
    def generate_rsa_keypair():
        """Generate RSA-4096 key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=config.RSA_KEY_SIZE,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    @staticmethod
    def encrypt_private_key_with_password(private_key_pem, password):
        """Encrypt private key using password (AES-256-GCM)"""
        # Generate salt
        salt = os.urandom(16)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        encryption_key = kdf.derive(password.encode())
        
        # Generate IV
        iv = os.urandom(12)
        
        # Encrypt
        ciphertext, tag = CryptoManager.encrypt_aes_gcm(
            private_key_pem.encode(),
            encryption_key,
            iv
        )
        
        # Combine salt + iv + tag + ciphertext
        encrypted_data = {
            'salt': CryptoManager.encode_base64(salt),
            'iv': CryptoManager.encode_base64(iv),
            'tag': CryptoManager.encode_base64(tag),
            'ciphertext': CryptoManager.encode_base64(ciphertext)
        }
        
        return encrypted_data
    
    @staticmethod
    def decrypt_private_key_with_password(encrypted_data, password):
        """Decrypt private key using password"""
        salt = CryptoManager.decode_base64(encrypted_data['salt'])
        iv = CryptoManager.decode_base64(encrypted_data['iv'])
        tag = CryptoManager.decode_base64(encrypted_data['tag'])
        ciphertext = CryptoManager.decode_base64(encrypted_data['ciphertext'])
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        encryption_key = kdf.derive(password.encode())
        
        # Decrypt
        plaintext = CryptoManager.decrypt_aes_gcm(ciphertext, encryption_key, iv, tag)
        
        return plaintext.decode('utf-8')