"""
Provably fair logic.

Commit-reveal scheme:
  1. Server generates server_seed at startup, publishes sha256(server_seed).
  2. Player sends SOL (the bet transaction gives a tx_signature).
  3. result = sha256(server_seed + ":" + tx_signature)
     Treat first 4 bytes as uint32 value in [0, 2^32).
     WIN if value < win_probability * 2^32.
  4. Server reveals server_seed on exit; anyone can verify.
"""
import hashlib
import secrets
import sys

_UINT32_MAX = 2**32


def new_server_seed() -> str:
    return secrets.token_hex(32)


def commitment(server_seed: str) -> str:
    return hashlib.sha256(server_seed.encode()).hexdigest()


def flip(server_seed: str, tx_signature: str, win_probability: float = 0.49) -> bool:
    """Return True if the player wins.

    Takes first 4 bytes of sha256(seed:sig) as a uint32, wins if it falls
    below win_probability * 2^32. This gives ~0.002% precision per step.
    """
    h = hashlib.sha256(f"{server_seed}:{tx_signature}".encode()).hexdigest()
    value = int(h[:8], 16)                        # uint32 in [0, 2^32)
    threshold = int(win_probability * _UINT32_MAX)
    return value < threshold


def verify_cli() -> None:
    print("Coin Flip Verifier")
    print("-" * 50)
    server_seed = input("Server seed (revealed after round ends):  ").strip()
    committed_hash = input("Server seed hash (published at startup):  ").strip()
    tx_sig = input("Transaction signature:                     ").strip()
    prob_str = input("Win probability (shown at startup) [0.49]: ").strip()
    win_probability = float(prob_str) if prob_str else 0.49

    actual_hash = commitment(server_seed)
    if actual_hash != committed_hash:
        print("\nFAIL: seed does not match the commitment.")
        print(f"  computed : {actual_hash}")
        print(f"  expected : {committed_hash}")
        sys.exit(1)

    print("\n✓ Server seed matches commitment")

    h = hashlib.sha256(f"{server_seed}:{tx_sig}".encode()).hexdigest()
    value = int(h[:8], 16)
    threshold = int(win_probability * _UINT32_MAX)
    won = value < threshold

    print(f"\nsha256(seed:sig) = {h}")
    print(f"uint32 value : {value} (0x{h[:8]})")
    print(f"threshold    : {threshold}  ({win_probability*100:.2f}% of 2^32)")
    print(f"value < threshold: {value} < {threshold} → {'WIN' if won else 'LOSE'}")
    print(f"\nResult: {'WIN ✓' if won else 'LOSE ✗'}")


if __name__ == "__main__":
    verify_cli()
