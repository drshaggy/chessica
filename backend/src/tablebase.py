import chess
import chess.syzygy
import aiohttp
import os
from typing import Optional

DATA_DIR = os.environ.get("DATA_DIR", "/data")
SYZYGY_DIR = os.path.join(DATA_DIR, "syzygy")

_tablebase: Optional[chess.syzygy.Tablebase] = None

def _get_local_tb() -> Optional[chess.syzygy.Tablebase]:
    global _tablebase
    if _tablebase is None and os.path.isdir(SYZYGY_DIR):
        try:
            tb = chess.syzygy.open_tablebase(SYZYGY_DIR)
            _tablebase = tb
        except Exception:
            pass
    return _tablebase

WDL_LABEL = {2: "win", 1: "cursed win", 0: "draw", -1: "blessed loss", -2: "loss"}

async def query_tablebase(fen: str) -> Optional[dict]:
    board = chess.Board(fen)
    piece_count = len(board.piece_map())

    if piece_count > 7:
        return None

    # Try local Syzygy first
    tb = _get_local_tb()
    if tb is not None:
        try:
            wdl = tb.probe_wdl(board)
            dtz = tb.probe_dtz(board)
            moves = []
            for move in board.legal_moves:
                board.push(move)
                try:
                    m_wdl = tb.probe_wdl(board)
                    moves.append({
                        "uci": move.uci(),
                        "san": board.san(move),
                        "wdl": WDL_LABEL.get(-m_wdl, "unknown"),
                        "wdl_raw": -m_wdl,
                    })
                except Exception:
                    pass
                finally:
                    board.pop()
            moves.sort(key=lambda m: m["wdl_raw"], reverse=True)
            return {
                "wdl": WDL_LABEL.get(wdl, "unknown"),
                "wdl_raw": wdl,
                "dtz": dtz,
                "moves": moves[:10],
                "source": "local",
            }
        except Exception:
            pass  # fall through to API

    # Fall back to Lichess tablebase API
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://tablebase.lichess.ovh/standard?fen={fen.replace(' ', '_')}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    moves = [
                        {
                            "uci": m["uci"],
                            "san": m.get("san", m["uci"]),
                            "wdl": _lichess_category(m.get("category", "")),
                            "dtz": m.get("dtz"),
                        }
                        for m in data.get("moves", [])[:10]
                    ]
                    return {
                        "wdl": _lichess_category(data.get("category", "")),
                        "dtz": data.get("dtz"),
                        "dtm": data.get("dtm"),
                        "moves": moves,
                        "source": "lichess",
                    }
    except Exception:
        pass

    return None

def _lichess_category(cat: str) -> str:
    mapping = {
        "win": "win", "maybe-win": "cursed win",
        "cursed-win": "cursed win", "draw": "draw",
        "blessed-loss": "blessed loss", "maybe-loss": "blessed loss",
        "loss": "loss",
    }
    return mapping.get(cat, cat)
