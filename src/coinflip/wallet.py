import base58
from solders.keypair import Keypair


def load_keypair(private_key_b58: str) -> Keypair:
    raw = base58.b58decode(private_key_b58)
    if len(raw) == 32:
        return Keypair.from_seed(raw)
    if len(raw) == 64:
        return Keypair.from_bytes(raw)
    raise ValueError(f"Invalid key length: {len(raw)} bytes (expected 32 or 64)")


def generate_and_print() -> None:
    kp = Keypair()
    key_b58 = base58.b58encode(bytes(kp)).decode()
    print("=" * 60)
    print("NEW SOLANA WALLET")
    print("=" * 60)
    print(f"Address (public key):  {kp.pubkey()}")
    print(f"Private key (base58):  {key_b58}")
    print()
    print("Add to your .env file:")
    print(f"  HOUSE_PRIVATE_KEY={key_b58}")
    print()
    print("WARNING: never share your private key!")
    print("=" * 60)


if __name__ == "__main__":
    generate_and_print()
