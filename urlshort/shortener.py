"""Base62 encoding helpers used to turn database ids into short codes."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(n: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return ALPHABET[0]
    chars = []
    while n:
        n, rem = divmod(n, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode(s: str) -> int:
    """Decode a base62 string back into an integer."""
    n = 0
    for ch in s:
        n = n * BASE + ALPHABET.index(ch)
    return n
