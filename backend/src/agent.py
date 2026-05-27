import asyncio
import json
import os
import chess

from dataclasses import dataclass
from typing import Optional

from .engine import get_engine
from .opening import get_book_moves
from .tablebase import query_tablebase

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "/usr/local/bin/claude")
CLAUDE_TOKEN = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

SKILL_LABELS = {
    "beginner": "~1320 Elo — play natural beginner moves, miss tactics",
    "novice": "~1500 Elo — play reasonable moves, occasional blunders",
    "intermediate": "~1700 Elo — solid club player, some missed tactics",
    "club": "~1900 Elo — strong club player, good positional play",
    "expert": "~2100 Elo — expert level, accurate but not perfect",
    "master": "~2400 Elo — master strength, very accurate",
    "grandmaster": "~2800 Elo — grandmaster level, near-perfect",
    "max": "Maximum strength — use Stockfish suggestions directly",
}

@dataclass
class AgentMove:
    uci: str
    san: str
    comment: Optional[str]
    updated_state: dict


def _move_history(board: chess.Board) -> str:  # exported for chat endpoint
    tmp = chess.Board()
    parts = []
    for i, move in enumerate(board.move_stack):
        san = tmp.san(move)
        tmp.push(move)
        if i % 2 == 0:
            parts.append(f"{i//2 + 1}. {san}")
        else:
            parts[-1] += f" {san}"
    return " ".join(parts) or "(game start)"


def _build_prompt(
    board: chess.Board,
    settings: dict,
    agent_state: dict,
    sf_lines: list[dict],
    book: list[dict],
    tb: Optional[dict],
) -> str:
    color = "black" if settings["player_color"] == "white" else "white"
    style = settings.get("style_prompt", "Play natural, principled chess.")
    level = settings.get("stockfish_level", "master")
    level_desc = SKILL_LABELS.get(level, level)
    phase = agent_state.get("phase", "opening")
    plan = agent_state.get("plan", "Develop pieces.")
    notes = agent_state.get("notes", [])
    book_line = agent_state.get("book_line", "")
    history = _move_history(board)

    sf_text = ""
    if sf_lines:
        sf_text = "Stockfish top lines:\n"
        for i, l in enumerate(sf_lines[:3]):
            score = f"M{l['score_mate']}" if l.get("score_mate") else f"{(l['score_cp'] or 0)/100:+.2f}"
            pv = " ".join(l.get("pv", [])[:4])
            sf_text += f"  {i+1}. {l.get('best_move','')} ({score}) — {pv}\n"

    book_text = ""
    if book:
        top = book[:6]
        book_text = "Opening book moves: " + ", ".join(f"{m['san']}({m['weight']})" for m in top)

    tb_text = ""
    if tb:
        tb_text = f"Tablebase: position is {tb['wdl'].upper()}"
        if tb.get("dtz"):
            tb_text += f" (DTZ {tb['dtz']})"
        if tb.get("moves"):
            best_tb = tb["moves"][0]
            tb_text += f". Best: {best_tb['san']} → {best_tb['wdl']}"

    notes_text = "\n".join(f"- {n}" for n in notes) if notes else "None."

    # Enumerate every legal move so Claude can only pick a real one
    legal = []
    for m in board.legal_moves:
        legal.append(f"{m.uci()} ({board.san(m)})")
    legal_str = "  " + "\n  ".join(legal)

    return f"""You are a chess grandmaster playing as {color.upper()}.

INSTRUCTIONS: {style}
STRENGTH: {level_desc}
PHASE: {phase}
OPENING: {book_line or 'not yet identified'}
YOUR PLAN: {plan}
GAME NOTES:
{notes_text}

POSITION (FEN): {board.fen()}
MOVE HISTORY: {history}

LEGAL MOVES (you MUST pick one of these exactly):
{legal_str}

CONTEXT:
{sf_text}{book_text}
{tb_text}

Honour your style instructions. At lower strength levels, play human-like moves rather than the engine top choice.
You MUST choose a move from the LEGAL MOVES list above — do not invent any other move.

Respond with ONLY a JSON object — no markdown, no explanation, just the raw JSON:
{{
  "move": "<UCI from the legal moves list above>",
  "comment": "<optional 1-2 sentence comment to show the player, or null>",
  "updated_state": {{
    "plan": "<your updated strategic plan>",
    "phase": "<opening|middlegame|endgame>",
    "notes": ["<keep only relevant notes, max 5>"]
  }}
}}"""


async def _call_claude(prompt: str, expect_json: bool = True):
    env = {**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": CLAUDE_TOKEN}
    proc = await asyncio.create_subprocess_exec(
        CLAUDE_BIN, "-p", prompt,
        "--output-format", "json",
        "--model", CLAUDE_MODEL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError("claude subprocess timed out after 90s")
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {stderr.decode()[:200]}")

    outer = json.loads(stdout.decode())
    raw = outer.get("result", "").strip()

    if not expect_json:
        return raw

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def get_ai_move(
    game_id: str,
    board: chess.Board,
    settings: dict,
    agent_state: dict,
) -> AgentMove:
    engine = get_engine()
    skill = settings.get("stockfish_level", "master")

    # Pre-compute context
    sf_lines = await engine.evaluate(board.fen(), depth=15, multipv=3)
    book = await get_book_moves(board.fen())
    tb = await query_tablebase(board.fen()) if len(board.piece_map()) <= 7 else None

    prompt = _build_prompt(board, settings, agent_state, sf_lines, book, tb)

    try:
        data = await _call_claude(prompt)
        uci = data.get("move", "")
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move: {uci}")
        return AgentMove(
            uci=uci,
            san=board.san(move),
            comment=data.get("comment"),
            updated_state=data.get("updated_state", agent_state),
        )
    except Exception as e:
        print(f"[agent] Claude error: {e} — falling back to Stockfish")
        uci = await engine.best_move(board.fen(), skill=skill)
        move = chess.Move.from_uci(uci)
        return AgentMove(
            uci=uci,
            san=board.san(move),
            comment=None,
            updated_state=agent_state,
        )
