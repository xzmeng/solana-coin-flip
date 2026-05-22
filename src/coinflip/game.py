"""
Provably fair logic.

Commit-reveal scheme:
  1. Server generates server_seed at startup, publishes sha256(server_seed).
  2. Player sends SOL (the bet transaction gives a tx_signature).
  3. result = sha256(server_seed + ":" + tx_signature)
     first byte < 128  →  WIN  (50 % chance)
  4. Server reveals server_seed on exit; anyone can verify.
"""
import hashlib
import secrets
import sys


def new_server_seed() -> str:
    return secrets.token_hex(32)


def commitment(server_seed: str) -> str:
    return hashlib.sha256(server_seed.encode()).hexdigest()


def flip(server_seed: str, tx_signature: str) -> bool:
    """Return True if the player wins."""
    h = hashlib.sha256(f"{server_seed}:{tx_signature}".encode()).hexdigest()
    return int(h[:2], 16) < 128


def verify_cli() -> None:
    print("Coin Flip Verifier")
    print("-" * 50)
    server_seed = input("Server seed (revealed after round ends): ").strip()
    committed_hash = input("Server seed hash (published at startup):  ").strip()
    tx_sig = input("Transaction signature:                     ").strip()

    actual_hash = commitment(server_seed)
    if actual_hash != committed_hash:
        print("\nFAIL: seed does not match the commitment.")
        print(f"  computed : {actual_hash}")
        print(f"  expected : {committed_hash}")
        sys.exit(1)

    print("\n✓ Server seed matches commitment")

    h = hashlib.sha256(f"{server_seed}:{tx_sig}".encode()).hexdigest()
    first_byte = int(h[:2], 16)
    won = first_byte < 128

    print(f"\nsha256(seed:sig) = {h}")
    print(f"First byte: 0x{h[:2]} = {first_byte}  ({'< 128 → WIN' if won else '>= 128 → LOSE'})")
    print(f"\nResult: {'WIN ✓' if won else 'LOSE ✗'}")


if __name__ == "__main__":
    verify_cli()
