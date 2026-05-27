import chess
import chess.polyglot
import json
import os
from typing import Optional

DATA_DIR = os.environ.get("DATA_DIR", "/data")
POLYGLOT_PATH = os.path.join(DATA_DIR, "openings", "performance.bin")
BOOK_PATH = os.path.join(DATA_DIR, "openings", "book.json")
ECO_PATH = os.path.join(DATA_DIR, "openings", "eco.json")

_eco: Optional[dict] = None
_book: Optional[dict] = None

def _load_eco() -> dict:
    global _eco
    if _eco is None:
        _eco = json.load(open(ECO_PATH)) if os.path.exists(ECO_PATH) else {}
    return _eco

def _load_book() -> dict:
    global _book
    if _book is None:
        _book = json.load(open(BOOK_PATH)) if os.path.exists(BOOK_PATH) else {}
    return _book

async def get_book_moves(fen: str) -> list[dict]:
    board = chess.Board(fen)
    fen_key = " ".join(board.fen().split()[:4])

    # Try local Polyglot binary first (if present and valid)
    if os.path.exists(POLYGLOT_PATH) and os.path.getsize(POLYGLOT_PATH) > 1000:
        try:
            moves = []
            with chess.polyglot.open_reader(POLYGLOT_PATH) as reader:
                for entry in reader.find_all(board):
                    moves.append({
                        "uci": entry.move.uci(),
                        "san": board.san(entry.move),
                        "weight": entry.weight,
                    })
            if moves:
                return sorted(moves, key=lambda m: m["weight"], reverse=True)
        except Exception:
            pass

    # Use local ECO-derived book
    book = _load_book()
    entries = book.get(fen_key, [])
    result = []
    for e in entries:
        try:
            move = chess.Move.from_uci(e["uci"])
            if move in board.legal_moves:
                result.append({
                    "uci": e["uci"],
                    "san": board.san(move),
                    "weight": e["weight"],
                })
        except Exception:
            pass
    return result

def get_opening_name(board: chess.Board) -> Optional[dict]:
    eco = _load_eco()
    fen_key = " ".join(board.fen().split()[:4])
    return eco.get(fen_key)

def find_opening_in_game(boards: list[chess.Board]) -> tuple[Optional[dict], int]:
    eco = _load_eco()
    if not eco:
        return None, 0
    for i in range(len(boards) - 1, -1, -1):
        fen_key = " ".join(boards[i].fen().split()[:4])
        match = eco.get(fen_key)
        if match:
            return match, i
    return None, 0
