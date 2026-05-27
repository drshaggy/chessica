import asyncio
import uuid
import chess
import chess.pgn
import io
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from . import db
from .agent import get_ai_move, _call_claude, _move_history
from .analysis import analyze_game
from .engine import get_engine, SKILL_PRESETS
from .opening import get_book_moves, get_opening_name
from .tablebase import query_tablebase

app = FastAPI(title="Chess AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.init_db()

@app.on_event("shutdown")
async def shutdown():
    await get_engine().close()


# ── Game management ──────────────────────────────────────────────────────────

class NewGameRequest(BaseModel):
    player_color: str = "white"          # white | black | random
    stockfish_level: str = "master"       # see SKILL_PRESETS keys
    style_prompt: str = "Play natural, principled chess."

class MoveRequest(BaseModel):
    uci: str

@app.get("/levels")
def get_levels():
    return list(SKILL_PRESETS.keys())

@app.post("/games")
async def create_game(req: NewGameRequest):
    import random
    color = req.player_color
    if color == "random":
        color = random.choice(["white", "black"])

    if req.stockfish_level not in SKILL_PRESETS:
        raise HTTPException(400, f"Unknown level. Choose from: {list(SKILL_PRESETS.keys())}")

    game_id = str(uuid.uuid4())[:8]
    settings = {
        "player_color": color,
        "stockfish_level": req.stockfish_level,
        "style_prompt": req.style_prompt,
    }
    await db.create_game(game_id, settings)

    # If player is black, AI moves first
    initial_ai_move = None
    if color == "black":
        board = chess.Board()
        game = await db.get_game(game_id)
        ai = await get_ai_move(game_id, board, settings, {})
        board.push(chess.Move.from_uci(ai.uci))
        pgn = _board_to_pgn(board)
        await db.update_game(game_id, pgn, "active", ai.updated_state)
        await db.add_move(game_id, 1, ai.san, ai.uci, board.fen(), comment=ai.comment)
        initial_ai_move = {"san": ai.san, "uci": ai.uci, "comment": ai.comment}

    return {"game_id": game_id, "player_color": color, "initial_ai_move": initial_ai_move}

@app.get("/games")
async def list_games():
    return await db.list_games()

@app.get("/games/{game_id}")
async def get_game(game_id: str):
    game = await db.get_game(game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    moves = await db.get_moves(game_id)
    board = _reconstruct_board(game["pgn"])
    book = await get_book_moves(board.fen())
    tb = await query_tablebase(board.fen()) if len(board.piece_map()) <= 7 else None
    return {
        **game,
        "moves": moves,
        "fen": board.fen(),
        "book_moves": book[:5],
        "tablebase": tb,
        "legal_moves": [m.uci() for m in board.legal_moves],
    }


@app.post("/games/{game_id}/move")
async def player_move(game_id: str, req: MoveRequest):
    game = await db.get_game(game_id)
    if not game:
        raise HTTPException(404)
    if game["status"] != "active":
        raise HTTPException(400, "Game is over")

    board = _reconstruct_board(game["pgn"])
    move = chess.Move.from_uci(req.uci)
    if move not in board.legal_moves:
        raise HTTPException(400, f"Illegal move: {req.uci}")

    san = board.san(move)
    ply = board.ply() + 1
    board.push(move)

    # Quick eval for the player's move
    engine = get_engine()
    eval_lines = await engine.evaluate(board.fen(), depth=14, multipv=1)
    eval_cp = eval_lines[0]["score_cp"] if eval_lines else None
    best_uci = eval_lines[0]["best_move"] if eval_lines else None

    is_book = req.uci in {m["uci"] for m in await get_book_moves(board.fen())}
    await db.add_move(game_id, ply, san, req.uci, board.fen(), eval_cp, best_uci, is_book)

    status = _game_status(board)
    pgn = _board_to_pgn(board)
    await db.update_game(game_id, pgn, status, game["agent_state"])

    if status != "active":
        return {"san": san, "fen": board.fen(), "status": status, "ai_move": None}

    # AI responds
    ai = await get_ai_move(game_id, board, game["settings"], game["agent_state"])
    ai_move = chess.Move.from_uci(ai.uci)
    ai_san = board.san(ai_move)
    ai_ply = board.ply() + 1
    board.push(ai_move)

    ai_eval = await engine.evaluate(board.fen(), depth=14, multipv=1)
    ai_eval_cp = ai_eval[0]["score_cp"] if ai_eval else None
    ai_best = ai_eval[0]["best_move"] if ai_eval else None

    ai_book = ai.uci in {m["uci"] for m in await get_book_moves(board.fen())}
    await db.add_move(game_id, ai_ply, ai_san, ai.uci, board.fen(), ai_eval_cp, ai_best, ai_book, ai.comment)

    status = _game_status(board)
    pgn = _board_to_pgn(board)

    # Update book line in agent state
    state = ai.updated_state
    opening = get_opening_name(board)
    if opening:
        state["book_line"] = f"{opening['eco']} {opening['name']}"

    await db.update_game(game_id, pgn, status, state)

    return {
        "san": san,
        "fen": board.fen(),
        "status": status,
        "eval_cp": eval_cp,
        "ai_move": {
            "san": ai_san,
            "uci": ai.uci,
            "comment": ai.comment,
            "eval_cp": ai_eval_cp,
        },
        "book_moves": (await get_book_moves(board.fen()))[:5],
        "tablebase": await query_tablebase(board.fen()) if len(board.piece_map()) <= 7 else None,
    }


# ── Analysis ─────────────────────────────────────────────────────────────────

_analysis_tasks: dict[str, str] = {}  # game_id -> "pending" | "done" | "error"

@app.post("/games/{game_id}/analyze")
async def request_analysis(game_id: str, background: BackgroundTasks):
    game = await db.get_game(game_id)
    if not game:
        raise HTTPException(404)

    existing = await db.get_analysis(game_id)
    if existing:
        return {"status": "done", "analysis": existing}

    if _analysis_tasks.get(game_id) == "pending":
        return {"status": "pending"}

    _analysis_tasks[game_id] = "pending"
    background.add_task(_run_analysis, game_id, game["pgn"])
    return {"status": "pending"}

@app.get("/games/{game_id}/analysis")
async def get_analysis_result(game_id: str):
    result = await db.get_analysis(game_id)
    if result:
        _analysis_tasks.pop(game_id, None)  # evict once persisted
        return {"status": "done", "analysis": result}
    status = _analysis_tasks.get(game_id, "not_started")
    return {"status": status}

async def _run_analysis(game_id: str, pgn: str):
    try:
        result = await analyze_game(pgn, game_id)
        await db.save_analysis(game_id, result)
        _analysis_tasks[game_id] = "done"
    except Exception as e:
        print(f"Analysis error for {game_id}: {e}")
        _analysis_tasks[game_id] = "error"


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

@app.post("/games/{game_id}/chat")
async def chat(game_id: str, req: ChatRequest):
    game = await db.get_game(game_id)
    if not game:
        raise HTTPException(404)

    board = _reconstruct_board(game["pgn"])
    engine = get_engine()
    sf_lines = await engine.evaluate(board.fen(), depth=15, multipv=3)
    book = await get_book_moves(board.fen())
    opening = get_opening_name(board)
    agent_state = game["agent_state"]
    settings = game["settings"]

    color_label = "White" if settings["player_color"] == "white" else "Black"
    ai_color = "Black" if settings["player_color"] == "white" else "White"
    history = _move_history(board)

    sf_text = ""
    if sf_lines:
        sf_text = "Stockfish evaluation:\n"
        for i, l in enumerate(sf_lines[:3]):
            score = f"M{l['score_mate']}" if l.get("score_mate") else f"{(l['score_cp'] or 0)/100:+.2f}"
            pv = " ".join(l.get("pv", [])[:5])
            sf_text += f"  Line {i+1}: {l.get('best_move','')} ({score}) — {pv}\n"

    book_text = ""
    if book:
        book_text = "Book moves here: " + ", ".join(f"{m['san']}" for m in book[:5])

    opening_text = f"{opening['eco']} {opening['name']}" if opening else agent_state.get("book_line", "unknown")
    plan = agent_state.get("plan", "")
    notes = agent_state.get("notes", [])
    notes_text = "\n".join(f"- {n}" for n in notes) if notes else "None."

    prompt = f"""You are a chess coach and the AI opponent in this game. You are playing as {ai_color}, the human is {color_label}.

GAME STATE:
- Opening: {opening_text}
- Position (FEN): {board.fen()}
- Move history: {history}
- Phase: {agent_state.get('phase', 'unknown')}
- Your current plan: {plan}
- Your notes on this game:
{notes_text}

{sf_text}
{book_text}

The human player asks: {req.message}

Give a SHORT, direct answer — 1-3 sentences maximum. Be specific to this position. Do not pad with caveats or lists.
If the question is simple (e.g. "what should I do?"), one crisp sentence is ideal.
Only go longer if the question explicitly asks for a detailed explanation."""

    try:
        data = await _call_claude(prompt, expect_json=False)
        return {"response": data}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Quick lookups ─────────────────────────────────────────────────────────────

@app.get("/book")
async def book_moves(fen: str):
    return await get_book_moves(fen)

@app.get("/tablebase")
async def tb_query(fen: str):
    result = await query_tablebase(fen)
    if result is None:
        raise HTTPException(404, "Position not in tablebase")
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reconstruct_board(pgn: str) -> chess.Board:
    if not pgn:
        return chess.Board()
    game = chess.pgn.read_game(io.StringIO(pgn))
    if not game:
        return chess.Board()
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    return board

def _board_to_pgn(board: chess.Board) -> str:
    game = chess.pgn.Game()
    node = game
    for move in board.move_stack:
        node = node.add_variation(move)
    return str(game)

def _game_status(board: chess.Board) -> str:
    if board.is_checkmate():
        return "black_won" if board.turn == chess.WHITE else "white_won"
    if board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves():
        return "draw"
    return "active"
