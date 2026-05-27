import asyncio
import chess
import chess.engine
import os
from typing import Optional

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")

SKILL_PRESETS = {
    "beginner":     {"Skill Level": 1,  "UCI_LimitStrength": True,  "UCI_Elo": 1320},
    "novice":       {"Skill Level": 5,  "UCI_LimitStrength": True,  "UCI_Elo": 1500},
    "intermediate": {"Skill Level": 10, "UCI_LimitStrength": True,  "UCI_Elo": 1700},
    "club":         {"Skill Level": 14, "UCI_LimitStrength": True,  "UCI_Elo": 1900},
    "expert":       {"Skill Level": 17, "UCI_LimitStrength": True,  "UCI_Elo": 2100},
    "master":       {"Skill Level": 19, "UCI_LimitStrength": True,  "UCI_Elo": 2400},
    "grandmaster":  {"Skill Level": 20, "UCI_LimitStrength": True,  "UCI_Elo": 2800},
    "max":          {"Skill Level": 20, "UCI_LimitStrength": False},
}

class StockfishEngine:
    def __init__(self):
        self._engine: Optional[chess.engine.UciProtocol] = None
        self._lock = asyncio.Lock()
        self._current_options: dict = {}

    async def _get_engine(self) -> chess.engine.UciProtocol:
        if self._engine is None:
            _, engine = await chess.engine.popen_uci(STOCKFISH_PATH)
            self._engine = engine
        return self._engine

    async def _apply_options(self, engine: chess.engine.UciProtocol, options: dict):
        changed = {k: v for k, v in options.items() if self._current_options.get(k) != v}
        if changed:
            await engine.configure(changed)
            self._current_options.update(changed)

    async def evaluate(
        self,
        fen: str,
        depth: int = 18,
        multipv: int = 1,
        skill: str = "max",
    ) -> list[dict]:
        async with self._lock:
            engine = await self._get_engine()
            opts = SKILL_PRESETS.get(skill, SKILL_PRESETS["max"]).copy()
            await self._apply_options(engine, opts)

            board = chess.Board(fen)
            result = await engine.analyse(
                board,
                chess.engine.Limit(depth=depth),
                multipv=multipv,
            )
            infos = result if isinstance(result, list) else [result]

            lines = []
            for info in infos:
                score = info.get("score")
                pv = info.get("pv", [])
                if score is None:
                    continue
                pov = score.white()
                lines.append({
                    "score_cp": pov.score(mate_score=10000),
                    "score_mate": pov.mate(),
                    "pv": [m.uci() for m in pv[:6]],
                    "best_move": pv[0].uci() if pv else None,
                })
            return lines

    async def best_move(self, fen: str, skill: str = "max", time_ms: int = 2000) -> Optional[str]:
        async with self._lock:
            engine = await self._get_engine()
            opts = SKILL_PRESETS.get(skill, SKILL_PRESETS["max"]).copy()
            opts.pop("MultiPV", None)
            await self._apply_options(engine, opts)

            board = chess.Board(fen)
            result = await engine.play(board, chess.engine.Limit(time=time_ms / 1000))
            return result.move.uci() if result.move else None

    async def close(self):
        if self._engine:
            await self._engine.quit()
            self._engine = None

_engine: Optional[StockfishEngine] = None

def get_engine() -> StockfishEngine:
    global _engine
    if _engine is None:
        _engine = StockfishEngine()
    return _engine
