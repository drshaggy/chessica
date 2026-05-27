import chess
import chess.pgn
import json
import io
from typing import Optional
import anthropic
import os

from .engine import get_engine
from .opening import find_opening_in_game, get_book_moves
from .tablebase import query_tablebase

_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.AsyncAnthropic(api_key=_token)
MODEL = "claude-sonnet-4-6"

BLUNDER_CP = 300
MISTAKE_CP = 150
INACCURACY_CP = 50

def _classify(delta_cp: int) -> str:
    if delta_cp >= BLUNDER_CP:
        return "blunder"
    if delta_cp >= MISTAKE_CP:
        return "mistake"
    if delta_cp >= INACCURACY_CP:
        return "inaccuracy"
    return "good"


async def analyze_game(pgn: str, game_id: str) -> dict:
    engine = get_engine()

    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return {}

    board = game.board()
    boards: list[chess.Board] = [board.copy()]
    moves_list = list(game.mainline_moves())

    for move in moves_list:
        board.push(move)
        boards.append(board.copy())

    # Opening detection
    opening, book_depth = find_opening_in_game(boards)

    # Per-move Stockfish analysis (full strength)
    move_analyses = []
    prev_score: Optional[int] = None

    for i, move in enumerate(moves_list):
        b_before = boards[i]
        b_after = boards[i + 1]

        lines = await engine.evaluate(b_before.fen(), depth=20, multipv=1, skill="max")
        score_before = lines[0]["score_cp"] if lines else 0
        best_uci = lines[0]["best_move"] if lines else None

        lines_after = await engine.evaluate(b_after.fen(), depth=20, multipv=1, skill="max")
        score_after = lines_after[0]["score_cp"] if lines_after else 0

        # Score is always from White's perspective
        if b_before.turn == chess.WHITE:
            delta = score_before - score_after  # white played, positive = lost advantage
        else:
            delta = score_after - score_before  # black played, positive = lost advantage

        classification = _classify(max(delta, 0))

        # Book move check
        book = await get_book_moves(b_before.fen())
        book_ucis = {m["uci"] for m in book}
        is_book = move.uci() in book_ucis

        # Tablebase check (only for endgame positions)
        tb = None
        if len(b_before.piece_map()) <= 7:
            tb = await query_tablebase(b_before.fen())

        move_analyses.append({
            "ply": i + 1,
            "san": b_before.san(move),
            "uci": move.uci(),
            "score_before": score_before,
            "score_after": score_after,
            "delta_cp": delta,
            "classification": classification,
            "best_uci": best_uci,
            "is_book": is_book,
            "tablebase": tb,
        })

        prev_score = score_after

    # Ask Claude for a narrative analysis
    narrative = await _generate_narrative(pgn, move_analyses, opening, book_depth)

    return {
        "opening_eco": opening["eco"] if opening else None,
        "opening_name": opening["name"] if opening else None,
        "book_depth": book_depth,
        "narrative": narrative,
        "moves": move_analyses,
    }


async def _generate_narrative(
    pgn: str,
    move_analyses: list[dict],
    opening: Optional[dict],
    book_depth: int,
) -> str:
    summary_lines = []
    for m in move_analyses:
        tag = f"[{m['classification'].upper()}]" if m["classification"] != "good" else ""
        tb = ""
        if m.get("tablebase"):
            tb = f" TB:{m['tablebase']['wdl']}"
        summary_lines.append(
            f"  Ply {m['ply']} {m['san']}{tag}: {m['score_before']:+d} → {m['score_after']:+d} cp{tb}"
        )
    summary = "\n".join(summary_lines)

    opening_str = f"{opening['eco']} {opening['name']} (book until move {book_depth // 2})" if opening else "No named opening detected"

    prompt = f"""Analyse this chess game and produce a tailored coaching narrative.

PGN:
{pgn}

Opening: {opening_str}

Move-by-move evaluation (cp = centipawns from White's perspective):
{summary}

Write a structured analysis covering:
1. **Opening** — what opening was played, where both sides followed or deviated from theory, key ideas
2. **Key moments** — the 2-4 most important turning points, quoting move numbers and explaining why
3. **Mistakes & Blunders** — explain each mistake/blunder in plain terms and what the better idea was
4. **Endgame** — if reached, how accurate was the technique? Include tablebase findings if relevant
5. **Summary** — 2-3 sentences: what went well, what to work on

Be specific, instructive, and honest. Refer to moves by number."""

    resp = await client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text
