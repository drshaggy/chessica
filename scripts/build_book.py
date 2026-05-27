"""
Builds a local opening book (book.json) from the ECO PGN data.
Maps FEN (4-part) -> list of {uci, san, count} moves.
"""
import json, os, chess, chess.pgn, io
from collections import defaultdict

DATA_DIR = os.environ.get("DATA_DIR", "/data")
ECO_PATH = os.path.join(DATA_DIR, "openings", "eco.json")
OUT = os.path.join(DATA_DIR, "openings", "book.json")

with open(ECO_PATH) as f:
    eco = json.load(f)

# fen_key -> {uci -> count}
book = defaultdict(lambda: defaultdict(int))

for fen_key, entry in eco.items():
    pgn_str = entry.get("pgn", "")
    if not pgn_str:
        continue
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if not game:
            continue
        board = game.board()
        for move in game.mainline_moves():
            pos_key = " ".join(board.fen().split()[:4])
            book[pos_key][move.uci()] += 1
            board.push(move)
    except Exception:
        continue

# Serialize: fen -> [{uci, san, weight}]
result = {}
start = chess.Board()
for pos_key, moves in book.items():
    # Reconstruct a board to get SAN — find any board matching this FEN key
    # We'll skip SAN here and let the caller compute it
    result[pos_key] = [
        {"uci": uci, "weight": count}
        for uci, count in sorted(moves.items(), key=lambda x: -x[1])
    ]

with open(OUT, "w") as f:
    json.dump(result, f)

print(f"Wrote {len(result)} positions to {OUT}")
