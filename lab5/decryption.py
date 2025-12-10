import numpy as np

from lab5.key_generator import McEliecePrivateKey, _mod2


def _invert_permutation_matrix(P: np.ndarray) -> np.ndarray:
    """
    Invert a permutation matrix.
    Over GF(2), P^{-1} = P^T.
    """
    return P.T


def _gaussian_elim_inverse_mod2(M: np.ndarray) -> np.ndarray:
    """
    Compute inverse of a k x k binary matrix over GF(2) using
    Gaussian elimination on [M | I].
    Raises ValueError if matrix is singular.
    """
    M = _mod2(M.copy())
    k = M.shape[0]
    I = np.eye(k, dtype=np.uint8)
    aug = np.concatenate([M, I], axis=1)  # [M | I]

    row = 0
    for col in range(k):
        # Find pivot
        pivot = None
        for r in range(row, k):
            if aug[r, col] == 1:
                pivot = r
                break
        if pivot is None:
            continue

        # Swap
        if pivot != row:
            aug[[row, pivot]] = aug[[pivot, row]]

        # Eliminate other rows
        for r in range(k):
            if r != row and aug[r, col] == 1:
                aug[r] ^= aug[row]

        row += 1
        if row == k:
            break

    # Check left side is identity
    if not np.array_equal(aug[:, :k], np.eye(k, dtype=np.uint8)):
        raise ValueError("Matrix is not invertible over GF(2)")

    return _mod2(aug[:, k:])


def _hamming_distance(a: np.ndarray, b: np.ndarray) -> int:
    """Hamming distance between two binary vectors."""
    return int(np.sum(a ^ b))


def _decode_c_hat(c_hat: np.ndarray, G: np.ndarray) -> np.ndarray:
    """
    Decoder for the secret code:
    brute-force all possible messages m in {0,1}^k,
    compute mG, and pick the one closest to c_hat.

    This is exponential in k; only for demonstration / small k.
    """
    k, n = G.shape
    best_m = None
    best_dist = n + 1

    # Enumerate all messages m as integers 0..2^k-1
    for x in range(1 << k):
        # Convert x to binary vector of length k
        bits = np.array(
            [(x >> i) & 1 for i in range(k)],
            dtype=np.uint8
        ).reshape(1, -1)  # row vector

        codeword = _mod2(bits @ G).reshape(-1)
        dist = _hamming_distance(codeword, c_hat)
        if dist < best_dist:
            best_dist = dist
            best_m = bits.reshape(-1)

        # small optimization: exact match
        if best_dist == 0:
            break

    return best_m  # length-k binary vector


def decrypt(private_key: McEliecePrivateKey, ciphertext: np.ndarray) -> np.ndarray:
    """
    Decrypt a ciphertext using the McEliece private key.

    Steps:
        1. c_hat = c * P^{-1}
        2. m_hat = Decode(c_hat) using secret code G
        3. S_inv = S^{-1}
        4. m = m_hat * S_inv
    """
    S = private_key.S
    P = private_key.P
    G = private_key.G

    k, n = G.shape
    c = ciphertext.reshape(1, -1)
    if c.shape[1] != n:
        raise ValueError(f"Ciphertext must have length {n}, got {c.shape[1]}")

    # 1. c_hat = c * P^{-1}
    P_inv = _invert_permutation_matrix(P)
    c_hat = _mod2(c @ P_inv).reshape(-1)  # length-n

    # 2. Decode c_hat to m_hat using the secret code
    m_hat = _decode_c_hat(c_hat, G)  # length-k

    # 3. Compute S^{-1} over GF(2)
    S_inv = _gaussian_elim_inverse_mod2(S)

    # 4. m = m_hat * S^{-1}
    m_hat_row = m_hat.reshape(1, -1)  # (1, k)
    m = _mod2(m_hat_row @ S_inv).reshape(-1)  # length-k

    return m
