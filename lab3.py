import random


def miller_rabin(n, k=40):
    """
    Function that tests if a number n is prime using the Miller-Rabin algorithm.

    :param n: The number to test (an integer).
    :param k: The number of rounds to perform (Higher k = more accuracy)

    :return: True if n is probably prime, False if n is definitely composite.
    """

    # Handle base cases for small numbers
    if n == 2 or n == 3:
        return True
    if n <= 1 or n % 2 == 0:
        return False

    # 1. Find s and t such that n - 1 = 2^s * t (with t odd)
    # We do this by repeatedly dividing n - 1 by 2
    t = n - 1
    s = 0
    while t % 2 == 0:
        t //= 2
        s += 1

    # 2. Perform k rounds of testing
    for _ in range(k):
        # 2a. Pick a random witness 'a' in the range [2, n - 2]
        a = random.randint(2, n - 2)

        # 2b. Compute x = a^t mod n
        # pow(base, exp, mod) is built-in and very efficient
        x = pow(a, t, n)

        # 2c. Check the first condition
        # If x is 1 or n-1, 'a' is not a witness,
        # so we continue to the next round.
        if x == 1 or x == n - 1:
            continue

        # 2d. The squaring loop
        # Repeat s-1 times: x = x^2 mod n
        # We are checking the sequence a^t, a^(2t), a^(4t), ...
        is_composite = True
        for _ in range(s - 1):
            x = pow(x, 2, n)

            # If we find n-1, 'a' is not a witness.
            # We break this inner loop and continue to the next 'a'.
            if x == n - 1:
                is_composite = False
                break

        # If the inner loop finished AND we never found x == n-1,
        # it means we found a non-trivial square root of 1.
        # This proves n is composite.
        if is_composite:
            return False

    # 3. If all k rounds passed, n is probably prime.
    return True

if __name__ == "__main__":
    # A small prime
    print(f"Is 13 prime? {miller_rabin(13)}")

    # A small composite
    print(f"Is 25 prime? {miller_rabin(25)}")

    # A Carmichael number (fools Fermat's test)
    print(f"Is 561 prime? {miller_rabin(561)}")

    # A large prime (Mersenne prime 2^61 - 1)
    large_prime = 2305843009213693951
    print(f"Is 2^61 - 1 prime? {miller_rabin(large_prime)}")

    # A large composite
    large_composite = large_prime + 2
    print(f"Is (2^61 - 1) + 2 prime? {miller_rabin(large_composite)}")