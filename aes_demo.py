"""Demo: AES symmetric encryption and decryption using the cryptography library."""

import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


def encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    """Encrypt plaintext with AES-CBC. Returns (iv, ciphertext)."""
    iv = os.urandom(16)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return iv, ciphertext


def decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt AES-CBC ciphertext. Returns plaintext."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def encrypt_ecb(plaintext: bytes, key: bytes) -> bytes:
    """Encrypt plaintext with AES-ECB (no IV). Returns ciphertext."""
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.ECB())
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def decrypt_ecb(ciphertext: bytes, key: bytes) -> bytes:
    """Decrypt AES-ECB ciphertext (no IV). Returns plaintext."""
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


if __name__ == "__main__":
    key = os.urandom(32)
    message = "Hello, this is a secret message!"
    print(f"Original:  {message}")

    # --- CBC (with IV) ---
    print("\n--- AES-CBC (with IV) ---")
    iv, ciphertext_cbc = encrypt(message.encode(), key)
    print(f"Key (hex): {key.hex()}")
    print(f"IV (hex):  {iv.hex()}")
    print(f"Encrypted: {ciphertext_cbc.hex()}")
    print(f"Decrypted: {decrypt(ciphertext_cbc, key, iv).decode()}")

    # --- ECB (no IV) ---
    print("\n--- AES-ECB (no IV) ---")
    ciphertext_ecb = encrypt_ecb(message.encode(), key)
    print(f"Key (hex): {key.hex()}")
    print(f"Encrypted: {ciphertext_ecb.hex()}")
    print(f"Decrypted: {decrypt_ecb(ciphertext_ecb, key).decode()}")
