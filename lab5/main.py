import numpy as np
from dataclasses import dataclass

from lab5.key_generator import (
    generate_mceliece_keys,
    McEliecePublicKey,
    McEliecePrivateKey,
)
from lab5.encryption import encrypt as _encrypt_binary
from lab5.decryption import decrypt as _decrypt_binary


ALPHABET = "_abcdefghijklmnopqrstuvwxyz"  # 27 symbols
CHAR_TO_IDX = {ch: i for i, ch in enumerate(ALPHABET)}
IDX_TO_CHAR = {i: ch for i, ch in enumerate(ALPHABET)}
BITS_PER_CHAR = 5  # 2^5 = 32 >= 27


def _validate_plaintext(plaintext: str) -> None:
    for ch in plaintext:
        if ch not in CHAR_TO_IDX:
            raise ValueError("Invalid character. Allowed: '_' and a-z only.")


def _validate_ciphertext(ciphertext: np.ndarray, n: int) -> None:
    if ciphertext.ndim not in (1, 2):
        raise ValueError("Ciphertext must be a 1-D or 2-D numpy array")
    if ciphertext.ndim == 1:
        if ciphertext.size != n:
            raise ValueError(f"Ciphertext must have length {n}, got {ciphertext.size}")
    else:
        if ciphertext.shape[1] != n:
            raise ValueError(f"Each ciphertext block must have length {n}, got {ciphertext.shape[1]}")
    if not np.all((ciphertext == 0) | (ciphertext == 1)):
        raise ValueError("Ciphertext must be binary (0/1)")


def _chars_to_bits(text: str) -> np.ndarray:
    """
    Encode text to a binary vector: 5 bits per character, LSB first per char.
    """
    bits_list: list[int] = []
    for ch in text:
        idx = CHAR_TO_IDX[ch]  # 0..26
        for i in range(BITS_PER_CHAR):
            bits_list.append((idx >> i) & 1)
    return np.array(bits_list, dtype=np.uint8)


def _bits_to_chars(bits: np.ndarray, num_chars: int) -> str:
    """
    Decode a binary vector to text: 5 bits per character, LSB first per char.
    Extra bits are ignored if bits.size > num_chars * BITS_PER_CHAR.
    """
    if bits.ndim != 1:
        raise ValueError("Bits must be a 1-D array")

    needed = num_chars * BITS_PER_CHAR
    if bits.size < needed:
        raise ValueError(
            f"Need at least {needed} bits to decode {num_chars} chars, got {bits.size}"
        )

    text_chars: list[str] = []
    for c in range(num_chars):
        start = c * BITS_PER_CHAR
        val = 0
        for i in range(BITS_PER_CHAR):
            b = int(bits[start + i])
            if b not in (0, 1):
                raise ValueError("Bits must be binary (0/1)")
            val |= (b << i)
        if val >= len(ALPHABET):
            val = 0
        text_chars.append(IDX_TO_CHAR[val])

    return "".join(text_chars)


@dataclass
class Alpha27PublicKey:
    mceliece_pk: McEliecePublicKey
    n: int
    k_bits: int
    k_chars: int  # number of characters per plaintext block


@dataclass
class Alpha27PrivateKey:
    mceliece_sk: McEliecePrivateKey
    n: int
    k_bits: int
    k_chars: int


def generate_alpha27_keys(n: int, k_chars: int, t: int) -> tuple[Alpha27PublicKey, Alpha27PrivateKey]:
    """
    k_chars: plaintext length (in characters) per block.
    McEliece parameter k = 5 * k_chars (bits).
    """
    k_bits = BITS_PER_CHAR * k_chars
    mceliece_pk, mceliece_sk = generate_mceliece_keys(n=n, k=k_bits, t=t)
    public_key = Alpha27PublicKey(mceliece_pk=mceliece_pk, n=n, k_bits=k_bits, k_chars=k_chars)
    private_key = Alpha27PrivateKey(mceliece_sk=mceliece_sk, n=n, k_bits=k_bits, k_chars=k_chars)
    return public_key, private_key


def encrypt_block(public_key: Alpha27PublicKey, block_text: str) -> np.ndarray:
    """
    Encrypt a single block of exactly k_chars characters.
    Assumes block_text already has the correct length.
    """
    k_chars = public_key.k_chars
    k_bits = public_key.k_bits

    if len(block_text) != k_chars:
        raise ValueError(f"Block must have length {k_chars}, got {len(block_text)}")

    _validate_plaintext(block_text)

    m_bits = _chars_to_bits(block_text)  # length k_bits
    if m_bits.size != k_bits:
        raise RuntimeError("Internal error: bit-length mismatch")

    c = _encrypt_binary(public_key.mceliece_pk, m_bits)
    return c


def decrypt_block(private_key: Alpha27PrivateKey, ciphertext_block: np.ndarray) -> str:
    """
    Decrypt a single ciphertext block (1-D array of length n) to k_chars characters.
    """
    n = private_key.n
    k_bits = private_key.k_bits
    k_chars = private_key.k_chars

    ciphertext_block = np.asarray(ciphertext_block, dtype=np.uint8).reshape(-1)
    _validate_ciphertext(ciphertext_block, n)

    m_bits = _decrypt_binary(private_key.mceliece_sk, ciphertext_block)
    if m_bits.size != k_bits:
        raise ValueError(f"Decrypted message length mismatch: expected {k_bits}, got {m_bits.size}")

    plaintext = _bits_to_chars(m_bits, k_chars)
    return plaintext


def encrypt_message(public_key: Alpha27PublicKey, plaintext: str) -> np.ndarray:
    """
    Encrypt an arbitrary-length plaintext.

    The plaintext is:
      * validated for allowed characters;
      * padded with '_' so its length is a multiple of k_chars;
      * split into blocks of length k_chars;
      * each block is encrypted to a ciphertext block of length n.

    Returns:
        2-D numpy array of shape (num_blocks, n), binary.
    """
    k_chars = public_key.k_chars
    n = public_key.n

    if len(plaintext) == 0:
        raise ValueError("Plaintext must not be empty")

    _validate_plaintext(plaintext)

    # Pad to a multiple of k_chars with '_'
    remainder = len(plaintext) % k_chars
    if remainder != 0:
        pad_len = k_chars - remainder
        plaintext = plaintext + "_" * pad_len

    num_blocks = len(plaintext) // k_chars
    blocks = [
        plaintext[i * k_chars:(i + 1) * k_chars]
        for i in range(num_blocks)
    ]

    ciphertext_blocks = []
    for block in blocks:
        c_block = encrypt_block(public_key, block)
        if c_block.size != n:
            raise RuntimeError("Internal error: ciphertext block length mismatch")
        ciphertext_blocks.append(c_block)

    return np.vstack(ciphertext_blocks)  # shape (num_blocks, n)


def decrypt_message(private_key: Alpha27PrivateKey, ciphertext: np.ndarray) -> str:
    """
    Decrypt an arbitrary-length ciphertext (multiple blocks).

    Input:
        ciphertext: 2-D numpy array of shape (num_blocks, n).
    Output:
        plaintext: concatenation of all decrypted blocks.
        No unpadding is done; the caller may strip trailing '_' if desired.
    """
    n = private_key.n

    ciphertext = np.asarray(ciphertext, dtype=np.uint8)
    if ciphertext.ndim == 1:
        # Single block case for convenience
        return decrypt_block(private_key, ciphertext)

    if ciphertext.ndim != 2:
        raise ValueError("Ciphertext must be a 2-D array for multi-block decryption")

    if ciphertext.shape[1] != n:
        raise ValueError(f"Each ciphertext block must have length {n}, got {ciphertext.shape[1]}")

    for i in range(ciphertext.shape[0]):
        _validate_ciphertext(ciphertext[i], n)

    plaintext_blocks = []
    for i in range(ciphertext.shape[0]):
        block_plain = decrypt_block(private_key, ciphertext[i])
        plaintext_blocks.append(block_plain)

    return "".join(plaintext_blocks)


if __name__ == "__main__":
    plaintext = "hello_world_this_is_a_long_message"

    n, k_chars, t = 30, 3, 2
    pk, sk = generate_alpha27_keys(n, k_chars, t)

    c = encrypt_message(pk, plaintext)
    print("Plaintext:", repr(plaintext))

    recovered = decrypt_message(sk, c)
    print("Recovered:", repr(recovered))
