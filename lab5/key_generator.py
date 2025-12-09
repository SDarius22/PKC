import numpy as np
from dataclasses import dataclass


def _mod2(mat: np.ndarray) -> np.ndarray:
    """Reduce matrix entries modulo 2."""
    return np.mod(mat, 2)


def _is_invertible_mod2(mat: np.ndarray) -> bool:
    """Check if a binary matrix is invertible over GF(2) via Gaussian elimination."""
    mat = _mod2(mat.copy())
    n = mat.shape[0]
    rank = 0

    for col in range(n):
        # Find pivot
        pivot = None
        for row in range(rank, n):
            if mat[row, col] == 1:
                pivot = row
                break
        if pivot is None:
            continue

        # Swap to current rank row
        if pivot != rank:
            mat[[rank, pivot]] = mat[[pivot, rank]]

        # Eliminate below
        for row in range(rank + 1, n):
            if mat[row, col] == 1:
                mat[row] ^= mat[rank]
        rank += 1

    return rank == n


def _random_invertible_matrix(k: int) -> np.ndarray:
    """Generate a random k x k invertible binary matrix over GF(2)."""
    while True:
        m = np.random.randint(0, 2, size=(k, k), dtype=np.uint8)
        if _is_invertible_mod2(m):
            return _mod2(m)


def _random_permutation_matrix(n: int) -> np.ndarray:
    """Generate a random n x n permutation matrix."""
    perm = np.random.permutation(n)
    P = np.zeros((n, n), dtype=np.uint8)
    P[np.arange(n), perm] = 1
    return P


def _generate_code_G(k: int, n: int) -> np.ndarray:
    """
    Placeholder for the secret code generator matrix G.

    For now, we just generate a random full-rank k x n binary matrix.
    In a real McEliece implementation, this would construct a specific
    family of codes (e.g., a binary Goppa code) and return its generator matrix.
    """
    if k > n:
        raise ValueError("Need k <= n")

    while True:
        G = np.random.randint(0, 2, size=(k, n), dtype=np.uint8)
        # Quick rank check over GF(2) using row-reduction
        if _matrix_rank_mod2(G) == k:
            return _mod2(G)


def _matrix_rank_mod2(mat: np.ndarray) -> int:
    """Compute rank of matrix over GF(2) via Gaussian elimination."""
    mat = _mod2(mat.copy())
    m, n = mat.shape
    rank = 0
    row = 0

    for col in range(n):
        if row >= m:
            break
        # Find pivot
        pivot = None
        for r in range(row, m):
            if mat[r, col] == 1:
                pivot = r
                break
        if pivot is None:
            continue

        # Swap rows
        if pivot != row:
            mat[[row, pivot]] = mat[[pivot, row]]

        # Eliminate below
        for r in range(row + 1, m):
            if mat[r, col] == 1:
                mat[r] ^= mat[row]

        rank += 1
        row += 1

    return rank


@dataclass
class McEliecePublicKey:
    """Public key: (G_hat, t)."""
    G_hat: np.ndarray  # k x n matrix over GF(2)
    t: int             # error-correcting capability


@dataclass
class McEliecePrivateKey:
    """Private key: (S, P, G). A represents the decoding algorithm parameters in a toy form."""
    S: np.ndarray      # k x k invertible matrix over GF(2)
    P: np.ndarray      # n x n permutation matrix
    G: np.ndarray      # k x n generator matrix of secret code
    t: int             # same t, to be used by the decoding algorithm


def generate_mceliece_keys(n: int, k: int, t: int) -> tuple[McEliecePublicKey, McEliecePrivateKey]:
    """
    Generate a toy McEliece key pair.

    Parameters:
        n: code length
        k: code dimension
        t: designed error-correcting capability

    Returns:
        (public_key, private_key)
    """
    if not (0 < k <= n):
        raise ValueError("Require 0 < k <= n")

    # 1. Secret code C with generator G
    G = _generate_code_G(k, n)

    # 2. Random invertible S (k x k)
    S = _random_invertible_matrix(k)

    # 3. Random permutation matrix P (n x n)
    P = _random_permutation_matrix(n)

    # 4. Public generator G_hat = S * G * P over GF(2)
    #    Note: multiplication is in integers, then reduced mod 2.
    G_hat = _mod2(S @ G @ P)

    public_key = McEliecePublicKey(G_hat=G_hat, t=t)
    private_key = McEliecePrivateKey(S=S, P=P, G=G, t=t)

    return public_key, private_key