# Toy McEliece Cryptosystem (27-symbol alphabet)

This project implements a **toy** McEliece-style public-key cryptosystem in Python using NumPy.  
It is **only for educational purposes** and must not be used for real security.

---

## 1. Overview

The system is a simplified McEliece scheme:

* Work over the binary field GF\(2\).
* Use a random binary \([n, k]\) linear code as the secret code.
* Wrap it with a 27-symbol plaintext alphabet:

  * `ALPHABET = "_abcdefghijklmnopqrstuvwxyz"`  
    (`_` = index 0, `a`..`z` = indices 1..26)

Plaintexts are split into fixed-size blocks of characters, encoded into bits, encrypted with the McEliece core, and reassembled for long messages.

---

## 2. Modules

* `lab5/key_generator.py`  
  Core key generation and linear-algebra helpers over GF\(2\).

* `lab5/encryption.py`  
  Binary McEliece encryption on bit-vectors.

* `lab5/decryption.py`  
  Binary McEliece decryption using a brute-force toy decoder.

* `lab5/main.py`  
  High-level 27-symbol alphabet interface:
  * character \<\-\> bit encoding,
  * block and multi-block encryption/decryption.

---

## 3. Alphabet and Encoding

In `lab5/main.py`:

* Alphabet:

  * `ALPHABET = "_abcdefghijklmnopqrstuvwxyz"`  
    27 symbols.

* Each character is encoded with `BITS_PER_CHAR = 5` bits  
  (since \(2^5 = 32 \ge 27\)).

* Encoding (`_chars_to_bits(text)`):

  * For each character `ch`, take `idx = CHAR_TO_IDX[ch]` in \[0, 26\].
  * Store `idx` as 5 bits, least-significant bit first.
  * A block of `k_chars` characters becomes a bit-vector of length `k_bits = 5 * k_chars`.

* Decoding (`_bits_to_chars(bits, num_chars)`):

  * Read 5 bits per character, reconstruct `val`.
  * If `val >= 27`, map to `0` (the `_` symbol).
  * Map back using `IDX_TO_CHAR[val]`.

Plaintext validation (`_validate_plaintext`) ensures all characters are in the allowed alphabet.

Ciphertext validation (`_validate_ciphertext`) ensures binary data and correct length/shape.

---

## 4. Key Generation

### 4.1 Binary McEliece keys (`lab5/key_generator.py`)

`generate_mceliece_keys(n: int, k: int, t: int)`

* Inputs:

  * `n` — code length (ciphertext length in bits).
  * `k` — code dimension (message length in bits).
  * `t` — designed error-correcting capability.

* Steps:

  1. Generate a random full-rank `k x n` binary matrix `G` (secret generator matrix).
  2. Generate a random invertible `k x k` binary matrix `S`.
  3. Generate a random `n x n` permutation matrix `P`.
  4. Compute public generator:

     * `G_hat = S @ G @ P mod 2`.

* Returns:

  * `McEliecePublicKey(G_hat, t)`
  * `McEliecePrivateKey(S, P, G, t)`

### 4.2 Alphabet-aware keys (`lab5/main.py`)

`generate_alpha27_keys(n: int, k_chars: int, t: int)`

* `k_chars`: number of characters per plaintext block.
* Internal `k_bits = 5 * k_chars`.
* Calls `generate_mceliece_keys(n, k_bits, t)` and wraps into:

  * `Alpha27PublicKey(mceliece_pk, n, k_bits, k_chars)`
  * `Alpha27PrivateKey(mceliece_sk, n, k_bits, k_chars)`

---

## 5. Encryption

### 5.1 Binary encryption (`lab5/encryption.py`)

`encrypt(public_key: McEliecePublicKey, message: Iterable[int])`

* Let `G_hat` be `k x n` from the public key.
* Normalize `message` to a length-`k` binary row vector (`_normalize_message`).
* Compute codeword:

  * `c_prime = m @ G_hat mod 2`.

* Sample random error vector `z` of length `n` and Hamming weight `t` (`_random_error_vector`).
* Output ciphertext:

  * `c = c_prime + z mod 2`.

Result: `n`-bit binary ciphertext.

### 5.2 High-level block encryption (`lab5/main.py`)

#### `encrypt_block(public_key: Alpha27PublicKey, block_text: str) -> np.ndarray`

* Input: `block_text` must have length exactly `k_chars`.
* Validate characters.
* Encode to bits via `_chars_to_bits` (length `k_bits`).
* Call binary `encrypt` to get an `n`-bit ciphertext block.

#### Long messages: `encrypt_message`

`encrypt_message(public_key: Alpha27PublicKey, plaintext: str) -> np.ndarray`

* Validate all characters.
* Pad plaintext with `_` so its length is a multiple of `k_chars`.
* Split into blocks of length `k_chars`.
* Encrypt each block with `encrypt_block`.
* Stack ciphertext blocks with `np.vstack`.

Return value:

* 2D NumPy array of shape `(num_blocks, n)`, binary.

---

## 6. Decryption

### 6.1 Binary decryption (`lab5/decryption.py`)

`decrypt(private_key: McEliecePrivateKey, ciphertext: np.ndarray) -> np.ndarray`

* Let private key contain `S`, `P`, `G` (all binary):

  1. Reshape ciphertext to `1 x n`, check length.
  2. Compute inverse permutation:

     * `P_inv = P.T` (permutation matrices are orthogonal over GF\(2\)).

  3. Remove permutation:

     * `c_hat = c @ P_inv mod 2`.

  4. Decode `c_hat` to a codeword of the secret code using `_toy_decode_c_hat`:

     * Brute-force all `m` in `{0,1}^k`.
     * Compute `m @ G mod 2` and pick the one with minimum Hamming distance to `c_hat`.

  5. Compute `S^{-1}` with `_gaussian_elim_inverse_mod2`.
  6. Recover original message bits:

     * `m = m_hat @ S^{-1} mod 2`.

Result: length-`k` binary message vector.

> The toy decoder is exponential in `k` and only suitable for very small parameters.

### 6.2 High-level block decryption (`lab5/main.py`)

#### `decrypt_block(private_key: Alpha27PrivateKey, ciphertext_block: np.ndarray) -> str`

* Validate that `ciphertext_block` is a binary vector of length `n`.
* Call binary `decrypt` to get `k_bits` bits.
* Convert bits back to `k_chars` characters with `_bits_to_chars`.

#### Long messages: `decrypt_message`

`decrypt_message(private_key: Alpha27PrivateKey, ciphertext: np.ndarray) -> str`

* If `ciphertext` is 1D (`shape == (n,)`), treat as a single block and call `decrypt_block`.
* If 2D (`shape == (num_blocks, n)`):

  * Validate each row via `_validate_ciphertext`.
  * Decrypt each block with `decrypt_block`.
  * Concatenate all block plaintexts.

No automatic unpadding is performed; the caller may strip trailing `_` characters if desired.

---

## 7. Example

Minimal usage via `lab5/main.py`:

```python
python
import numpy as np
from lab5.main import generate_alpha27_keys, encrypt_message, decrypt_message

plaintext = "hello_world_this_is_a_long_message"

# Parameters: n = ciphertext bits per block, k_chars = chars per block, t = errors per block
n, k_chars, t = 30, 3, 2
pk, sk = generate_alpha27_keys(n, k_chars, t)

ciphertext = encrypt_message(pk, plaintext)
print("Ciphertext shape:", ciphertext.shape)  # (num_blocks, n)

recovered = decrypt_message(sk, ciphertext)
print("Recovered:", recovered)  # includes any '_' padding at the end
