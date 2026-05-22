from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from .config import get_config
from .wallet import load_keypair

app = FastAPI()

_TEMPLATES = Path(__file__).parent / "templates"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_TEMPLATES / "index.html")


@app.get("/api/info")
async def info() -> JSONResponse:
    cfg = get_config()
    kp = load_keypair(cfg.house_private_key)
    return JSONResponse({
        "house_address": str(kp.pubkey()),
        "network": cfg.network,
        "win_pct": round(cfg.win_probability * 100, 2),
        "min_bet_sol": cfg.min_bet_lamports / 1_000_000_000,
    })


def main() -> None:
    uvicorn.run("coinflip.web:app", host="0.0.0.0", port=8000, reload=True)
