import aiosqlite
import json
import os
from typing import Optional

DB_PATH = os.path.join(os.environ.get("DATA_DIR", "/data"), "chess.db")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now')),
    settings TEXT NOT NULL,       -- JSON
    pgn TEXT DEFAULT '',
    status TEXT DEFAULT 'active', -- active | white_won | black_won | draw
    agent_state TEXT DEFAULT '{}'  -- JSON
);

CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    ply INTEGER NOT NULL,
    san TEXT NOT NULL,
    uci TEXT NOT NULL,
    fen_after TEXT NOT NULL,
    eval_cp INTEGER,
    best_uci TEXT,
    is_book INTEGER DEFAULT 0,
    comment TEXT,
    FOREIGN KEY (game_id) REFERENCES games(id)
);

CREATE TABLE IF NOT EXISTS analysis (
    game_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now')),
    opening_eco TEXT,
    opening_name TEXT,
    book_depth INTEGER,
    narrative TEXT,
    moves_json TEXT,  -- per-move analysis array
    FOREIGN KEY (game_id) REFERENCES games(id)
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()

async def create_game(game_id: str, settings: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO games (id, settings) VALUES (?, ?)",
            (game_id, json.dumps(settings))
        )
        await db.commit()

async def get_game(game_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM games WHERE id = ?", (game_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "created_at": row["created_at"],
                "settings": json.loads(row["settings"]),
                "pgn": row["pgn"],
                "status": row["status"],
                "agent_state": json.loads(row["agent_state"]),
            }

async def list_games() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, created_at, settings, status FROM games ORDER BY created_at DESC LIMIT 50"
        ) as cur:
            rows = await cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "created_at": r["created_at"],
                    "settings": json.loads(r["settings"]),
                    "status": r["status"],
                }
                for r in rows
            ]

async def update_game(game_id: str, pgn: str, status: str, agent_state: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE games SET pgn=?, status=?, agent_state=? WHERE id=?",
            (pgn, status, json.dumps(agent_state), game_id)
        )
        await db.commit()

async def add_move(
    game_id: str, ply: int, san: str, uci: str, fen_after: str,
    eval_cp: Optional[int] = None, best_uci: Optional[str] = None,
    is_book: bool = False, comment: Optional[str] = None
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO moves (game_id,ply,san,uci,fen_after,eval_cp,best_uci,is_book,comment) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (game_id, ply, san, uci, fen_after, eval_cp, best_uci, int(is_book), comment)
        )
        await db.commit()

async def get_moves(game_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM moves WHERE game_id=? ORDER BY ply", (game_id,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

async def save_analysis(game_id: str, data: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO analysis (game_id,opening_eco,opening_name,book_depth,narrative,moves_json) "
            "VALUES (?,?,?,?,?,?)",
            (
                game_id,
                data.get("opening_eco"),
                data.get("opening_name"),
                data.get("book_depth", 0),
                data.get("narrative"),
                json.dumps(data.get("moves", [])),
            )
        )
        await db.commit()

async def get_analysis(game_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM analysis WHERE game_id=?", (game_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return {
                "opening_eco": row["opening_eco"],
                "opening_name": row["opening_name"],
                "book_depth": row["book_depth"],
                "narrative": row["narrative"],
                "moves": json.loads(row["moves_json"] or "[]"),
            }
