"""
Downloads Lichess opening TSV files and builds a FEN-keyed JSON for fast lookup.
Runs once at container startup.
"""
import json
import os
import urllib.request
import chess
import chess.pgn
import io

DATA_DIR = os.environ.get("DATA_DIR", "/data")
OUT = os.path.join(DATA_DIR, "openings", "eco.json")

URLS = [
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/a.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/b.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/c.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/d.tsv",
    "https://raw.githubusercontent.com/lichess-org/chess-openings/master/e.tsv",
]

openings = {}  # fen_key (first 4 parts) -> {eco, name, pgn}

def pgn_to_fen(pgn_moves: str) -> str | None:
    try:
        game = chess.pgn.read_game(io.StringIO(f"[FEN \"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\"]\n\n{pgn_moves}"))
        if not game:
            return None
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        return " ".join(board.fen().split()[:4])
    except Exception:
        return None

for url in URLS:
    print(f"Fetching {url}...")
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            lines = r.read().decode().splitlines()
            # header: eco\tname\tpgn
            for line in lines[1:]:
                parts = line.strip().split("\t")
                if len(parts) < 3:
                    continue
                eco, name, pgn = parts[0], parts[1], parts[2]
                fen_key = pgn_to_fen(pgn)
                if fen_key:
                    openings[fen_key] = {"eco": eco, "name": name, "pgn": pgn}
    except Exception as e:
        print(f"  Failed: {e}")

with open(OUT, "w") as f:
    json.dump(openings, f)

print(f"Wrote {len(openings)} openings to {OUT}")
