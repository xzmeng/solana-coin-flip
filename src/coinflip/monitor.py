import asyncio
import base64
import hashlib
import signal
import sys
from datetime import datetime

import httpx
from rich.console import Console
from rich.panel import Panel
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

from .config import get_config
from .game import commitment, flip, new_server_seed
from .wallet import load_keypair

console = Console()


# ---------------------------------------------------------------------------
# JSON-RPC client
# ---------------------------------------------------------------------------

class SolanaRPC:
    def __init__(self, url: str) -> None:
        self.url = url
        self._id = 0

    async def _call(self, method: str, *params) -> object:
        self._id += 1
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                self.url,
                json={"jsonrpc": "2.0", "id": self._id, "method": method, "params": list(params)},
            )
            data = resp.json()
        if "error" in data:
            raise RuntimeError(f"RPC {method}: {data['error']}")
        return data["result"]

    async def get_signatures(self, address: str, limit: int = 20) -> list[dict]:
        return await self._call("getSignaturesForAddress", address, {"limit": limit})  # type: ignore[return-value]

    async def get_transaction(self, sig: str) -> dict | None:
        return await self._call(  # type: ignore[return-value]
            "getTransaction",
            sig,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"},
        )

    async def get_balance(self, address: str) -> int:
        result = await self._call("getBalance", address, {"commitment": "confirmed"})
        return result["value"]  # type: ignore[index]

    async def get_latest_blockhash(self) -> str:
        result = await self._call("getLatestBlockhash", {"commitment": "confirmed"})
        return result["value"]["blockhash"]  # type: ignore[index]

    async def send_transaction(self, tx_b64: str) -> str:
        return await self._call("sendTransaction", tx_b64, {"encoding": "base64"})  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Transaction parsing
# ---------------------------------------------------------------------------

def _key_str(k: dict | str) -> str:
    return k["pubkey"] if isinstance(k, dict) else k


def parse_incoming_sol(tx: dict | None, house_address: str) -> tuple[str, int] | None:
    """Return (sender_address, lamports_received) for a SOL transfer to house, else None."""
    if tx is None or tx.get("meta", {}).get("err") is not None:
        return None

    keys: list = tx["transaction"]["message"]["accountKeys"]
    pre: list[int] = tx["meta"]["preBalances"]
    post: list[int] = tx["meta"]["postBalances"]

    house_idx = next((i for i, k in enumerate(keys) if _key_str(k) == house_address), None)
    if house_idx is None:
        return None

    received = post[house_idx] - pre[house_idx]
    if received <= 0:
        return None

    sender = _key_str(keys[0])
    if sender == house_address:
        return None  # outgoing tx from house

    return sender, received


# ---------------------------------------------------------------------------
# Payout
# ---------------------------------------------------------------------------

async def send_payout(rpc: SolanaRPC, house_kp: Keypair, winner: str, lamports: int) -> str:
    blockhash = await rpc.get_latest_blockhash()
    ix = transfer(TransferParams(
        from_pubkey=house_kp.pubkey(),
        to_pubkey=Pubkey.from_string(winner),
        lamports=lamports,
    ))
    msg = MessageV0.try_compile(
        payer=house_kp.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=Hash.from_string(blockhash),
    )
    tx = VersionedTransaction(msg, [house_kp])
    tx_b64 = base64.b64encode(bytes(tx)).decode()
    return await rpc.send_transaction(tx_b64)


# ---------------------------------------------------------------------------
# Main monitor loop
# ---------------------------------------------------------------------------

async def run_monitor(
    rpc: SolanaRPC,
    house_kp: Keypair,
    server_seed: str,
    min_bet: int,
    poll: int,
    win_probability: float,
) -> None:
    house_addr = str(house_kp.pubkey())
    seen: set[str] = set()

    existing = await rpc.get_signatures(house_addr, limit=100)
    for s in existing:
        seen.add(s["signature"])
    console.print(f"Skipped [dim]{len(seen)}[/] existing transactions — watching for new bets…\n")

    while True:
        try:
            sigs = await rpc.get_signatures(house_addr, limit=20)
            new_sigs = [s for s in reversed(sigs) if s["signature"] not in seen]

            for sig_info in new_sigs:
                sig: str = sig_info["signature"]
                seen.add(sig)

                tx = await rpc.get_transaction(sig)
                parsed = parse_incoming_sol(tx, house_addr)
                if parsed is None:
                    continue

                sender, lamports = parsed
                ts = datetime.now().strftime("%H:%M:%S")

                if lamports < min_bet:
                    console.print(
                        f"[dim][{ts}] {sig[:16]}… {lamports/1e9:.6f} SOL below minimum, ignored[/]"
                    )
                    continue

                won = flip(server_seed, sig, win_probability)
                result_hex = hashlib.sha256(f"{server_seed}:{sig}".encode()).hexdigest()

                if won:
                    payout = lamports * 2
                    balance = await rpc.get_balance(house_addr)
                    if balance < payout + 10_000:
                        console.print(
                            f"[bold red][{ts}] WIN but house balance too low "
                            f"(need {payout/1e9:.4f} SOL, have {balance/1e9:.4f} SOL)[/]"
                        )
                        continue
                    payout_sig = await send_payout(rpc, house_kp, sender, payout)
                    console.print(
                        f"[bold green][{ts}] WIN [/] {sender[:8]}… "
                        f"bet [cyan]{lamports/1e9:.4f}[/] → paid [cyan]{payout/1e9:.4f} SOL[/]  "
                        f"hash={result_hex[:16]}…"
                    )
                    console.print(f"          payout tx: {payout_sig[:20]}…")
                else:
                    console.print(
                        f"[bold red][{ts}] LOSE[/] {sender[:8]}… "
                        f"bet [cyan]{lamports/1e9:.4f} SOL[/] → kept  "
                        f"hash={result_hex[:16]}…"
                    )

        except Exception as exc:
            console.print(f"[red]Poll error: {exc}[/]")

        await asyncio.sleep(poll)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = get_config()
    house_kp = load_keypair(cfg.house_private_key)
    house_addr = str(house_kp.pubkey())

    server_seed = new_server_seed()
    seed_hash = commitment(server_seed)

    rpc = SolanaRPC(cfg.rpc_url)

    console.print(Panel.fit(
        f"[bold]Network:[/]          [cyan]{cfg.network}[/]\n"
        f"[bold]House address:[/]    [cyan]{house_addr}[/]\n"
        f"[bold]Win probability:[/]  [cyan]{cfg.win_probability*100:.2f}%[/]\n"
        f"[bold]Min bet:[/]          [cyan]{cfg.min_bet_lamports / 1e9:.4f} SOL[/]\n"
        f"[bold]Poll interval:[/]    [cyan]{cfg.poll_interval}s[/]\n\n"
        f"[bold yellow]Server seed hash:[/]  [yellow]{seed_hash}[/]\n"
        f"[dim]Share address, win probability, and seed hash with players before they bet.\n"
        f"The seed is revealed on exit so anyone can verify results.[/]",
        title="[bold green]Solana Coin Flip[/]",
    ))

    def _on_exit(*_: object) -> None:
        console.print(f"\n[bold yellow]Server seed revealed:[/] [yellow]{server_seed}[/]")
        console.print("Players can verify any result with: [cyan]uv run coinflip-verify[/]")
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_exit)
    try:
        signal.signal(signal.SIGTERM, _on_exit)
    except (AttributeError, OSError):
        pass

    asyncio.run(run_monitor(rpc, house_kp, server_seed, cfg.min_bet_lamports, cfg.poll_interval, cfg.win_probability))


if __name__ == "__main__":
    main()
