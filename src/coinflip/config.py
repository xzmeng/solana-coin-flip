import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_RPC_URLS = {
    "devnet": "https://api.devnet.solana.com",
    "testnet": "https://api.testnet.solana.com",
    "mainnet-beta": "https://api.mainnet-beta.solana.com",
}


@dataclass
class Config:
    network: str
    rpc_url: str
    house_private_key: str
    poll_interval: int
    min_bet_lamports: int


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = _load()
    return _config


def _load() -> Config:
    network = os.getenv("NETWORK", "devnet")
    rpc_url = os.getenv("RPC_URL") or _RPC_URLS.get(network)
    if not rpc_url:
        raise SystemExit(
            f"Unknown NETWORK '{network}'. Use devnet, testnet, mainnet-beta, or set RPC_URL."
        )

    key = os.getenv("HOUSE_PRIVATE_KEY", "").strip()
    if not key:
        raise SystemExit(
            "HOUSE_PRIVATE_KEY not set in .env.\n"
            "Run `uv run coinflip-new-wallet` to generate a wallet."
        )

    return Config(
        network=network,
        rpc_url=rpc_url,
        house_private_key=key,
        poll_interval=int(os.getenv("POLL_INTERVAL_SECONDS", "5")),
        min_bet_lamports=int(os.getenv("MIN_BET_LAMPORTS", "1000000")),
    )
