from math import gcd, log
from lab3 import miller_rabin

import random

alphabet = "_abcdefghijklmnopqrstuvwxyz"
alphabet_map = {char: idx for idx, char in enumerate(alphabet)}

def random_prime(length = 16):
    while True:
        # Generate a random odd number with the specified bit length
        num = random.getrandbits(length) | 1 | (1 << (length - 1))

        # Test for primality using Miller-Rabin
        if miller_rabin(num, k=40):
            return num

def randomly_select_e(phi_n):
    while True:
        e = random.randrange(2, phi_n-1)
        if gcd(e, phi_n) == 1:
            return e

def numerical_to_literal(num: int, length: int) -> str:
    chars = []
    for i in range(length):
        remainder = num % 27
        chars.append(alphabet[remainder])
        num //= 27
    chars.reverse()
    return ''.join(chars)

def encrypt(message: str, e: int, n: int, k: int, l: int) -> str:
    # split message into blocks of length k
    message_to_nums = [alphabet_map[char] for char in message]
    blocks = []
    for i in range(0, len(message_to_nums), k):
        block = message_to_nums[i:i+k]
        blocks.append(block)

    numerical_equivalents = []
    for block in blocks:
        num = 0
        for idx, val in enumerate(block):
            num += val * (27 ** (k - idx - 1))
        numerical_equivalents.append(num)

    encrypted_blocks = []
    for num in numerical_equivalents:
        cipher_num = pow(num, e, n)
        encrypted_blocks.append(cipher_num)

    # return the literal equivalent of the encrypted blocks in base 27 with length l
    encrypted_message = ""
    for cipher_num in encrypted_blocks:
        encrypted_message += numerical_to_literal(cipher_num, l)
    return encrypted_message


def decrypt(encrypted_message: str, d: int, n: int, k: int, l: int) -> str:
    # split encrypted message into blocks of length l
    blocks = []
    for i in range(0, len(encrypted_message), l):
        block = encrypted_message[i:i+l]
        blocks.append(block)

    numerical_equivalents = []
    for block in blocks:
        num = 0
        for idx, char in enumerate(block):
            num += alphabet_map[char] * (27 ** (l - idx - 1))
        numerical_equivalents.append(num)

    decrypted_blocks = []
    for cipher_num in numerical_equivalents:
        plain_num = pow(cipher_num, d, n)
        decrypted_blocks.append(plain_num)

    # convert numerical equivalents back to message
    decrypted_message = ""
    for plain_num in decrypted_blocks:
        decrypted_message += numerical_to_literal(plain_num, k)
    return decrypted_message.strip()






if __name__ == "__main__":
    p = random_prime()
    q = random_prime()
    print(f"p = {p}")
    print(f"q = {q}")
    n = p * q
    print(f"n = p * q = {n}")
    phi_n = (p - 1) * (q - 1)
    print(f"φ(n) = (p - 1)(q - 1) = {phi_n}")
    e = randomly_select_e(phi_n)
    print(f"e = {e}")
    d = pow(e, -1, phi_n)
    print(f"d = {d}")

    # we need to find k and l, such that 27 ** k < n and 27 ** l
    k = int(log(n, 27)) - 1 if log(n, 27).is_integer() else int(log(n, 27))
    l = int(log(n, 27)) + 1
    # print(f"Maximum message length k (in base 27) is: {k}")
    # print(f"Minimum ciphertext length l (in base 27) is: {l}")

    # encryption
    message = "hello_world"

    # pad message to be multiple of k
    while len(message) % k != 0:
        message += "_"
    print(f"Original message: {message}")

    encrypted_message = encrypt(message, e, n, k, l)
    print(f"Encrypted message: {encrypted_message.upper()}")

    # decryption

    decrypted_message = decrypt(encrypted_message, d, n, k, l)
    print(f"Decrypted message: {decrypted_message}")




