from math import gcd

def generators(n: int) -> list[int]:
    """
    Function that returns all generators of the cyclic group (Zn, +)

    A generator of (Zn, +) is an element ˆg ∈ Zn such that for every ˆx ∈ Zn there is k ∈ {0, 1, . . . , n − 1} such
    that ˆx = kˆg

    Theorem: An element ˆg ∈ Zn is a generator of (Zn, +) if and only if gcd(ˆg, n) = 1.

    :param n: natural number n
    :return: list of generators of the cyclic group (Zn, +)
    """
    if n < 2:
        raise ValueError("n must be a natural number (n >= 2)")

    return [i for i in range(1, n) if gcd(i, n) == 1]

def main():
    n = int(input("Enter a natural number n (n >= 2): "))
    try:
        gens = generators(n)
        print(f"The generators of the cyclic group (Z{n}, +) are: {gens}")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()