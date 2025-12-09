import numpy as np
from typing import Iterable

from lab5.key_generator import McEliecePublicKey
from lab5.key_generator import _mod2  # reuse helper if you want; or reimplement mod2 here


def _random_error_vector(n: int, t: int) -> np.ndarray:
    """
    Generate a random binary vector of length n and Hamming weight exactly t.
    """
    if not (0 <= t <= n):
        raise ValueError("Require 0 <= t <= n")
    z = np.zeros(n, dtype=np.uint8)
    positions = np.random.choice(n, size=t, replace=False)
    z[positions] = 1
    return z


def _normalize_message(m: Iterable[int], k: int) -> np.ndarray:
    """
    Convert message to a length-k binary row vector over GF(2).
    """
    m_arr = np.fromiter(m, dtype=np.uint8, count=-1)
    if m_arr.size != k:
        raise ValueError(f"Message must have length {k}, got {m_arr.size}")
    if not np.all((m_arr == 0) | (m_arr == 1)):
        raise ValueError("Message must be binary (0/1)")
    return m_arr


def encrypt(public_key: McEliecePublicKey, message: Iterable[int]) -> np.ndarray:
    """
    Encrypt a binary message using the McEliece public key.

    Parameters:
        public_key: McEliecePublicKey with G_hat (k x n) and t.
        message: iterable of 0/1 of length k.

    Returns:
        Ciphertext vector c of length n over GF(2).
    """
    G_hat = public_key.G_hat
    t = public_key.t
    k, n = G_hat.shape

    # 1. Normalize/validate message (1 x k row vector).
    m = _normalize_message(message, k)  # shape (k,)
    m_row = m.reshape(1, -1)            # shape (1, k)

    # 2. Compute c' = m * G_hat over GF(2).
    c_prime = _mod2(m_row @ G_hat).reshape(-1)  # shape (n,)

    # 3. Sample random error vector z of weight t.
    z = _random_error_vector(n, t)

    # 4. Ciphertext c = c' + z over GF(2).
    c = _mod2(c_prime + z)
    return c


if __name__ == "__main__":
    # Small manual test (using the toy key generator).
    from lab5.key_generator import generate_mceliece_keys

    n, k, t = 10, 5, 2
    pk, sk = generate_mceliece_keys(n, k, t)

    # Example random message of length k.
    m = np.random.randint(0, 2, size=k, dtype=np.uint8)

    c = encrypt(pk, m)
    print("Message m:     ", m)
    print("Ciphertext c:  ", c)
    print("Ciphertext len:", c.size)
