import { useState, useCallback } from 'react'
import { Chess } from 'chess.js'
import { api } from '../api'
import type { GameState, MoveRecord } from '../types'

export interface GameHookState {
  gameId: string | null
  game: Chess
  gameData: GameState | null
  moves: MoveRecord[]
  status: string
  waiting: boolean
  error: string | null
  lastComment: string | null
  evalHistory: { ply: number; cp: number }[]
}

export function useGame() {
  const [state, setState] = useState<GameHookState>({
    gameId: null,
    game: new Chess(),
    gameData: null,
    moves: [],
    status: 'idle',
    waiting: false,
    error: null,
    lastComment: null,
    evalHistory: [],
  })

  const startGame = useCallback(async (settings: import('../types').GameSettings) => {
    setState(s => ({ ...s, waiting: true, error: null }))
    try {
      const res = await api.createGame(settings)
      const gameData = await api.getGame(res.game_id)
      const game = new Chess()

      if (res.initial_ai_move) {
        const aiMove = res.initial_ai_move as { uci: string; comment: string | null }
        game.move({ from: aiMove.uci.slice(0, 2), to: aiMove.uci.slice(2, 4), promotion: aiMove.uci[4] })
      }

      setState(s => ({
        ...s,
        gameId: res.game_id,
        game,
        gameData,
        moves: gameData.moves,
        status: 'active',
        waiting: false,
        lastComment: res.initial_ai_move
          ? (res.initial_ai_move as { comment: string | null }).comment
          : null,
        evalHistory: [],
      }))
    } catch (e) {
      setState(s => ({ ...s, waiting: false, error: String(e) }))
    }
  }, [])

  const makeMove = useCallback(async (uci: string) => {
    if (!state.gameId || state.waiting) return

    // Optimistic update — show the player's move immediately
    const optimisticGame = new Chess(state.game.fen())
    const moved = optimisticGame.move({
      from: uci.slice(0, 2),
      to: uci.slice(2, 4),
      promotion: uci[4] || 'q',
    })
    if (!moved) return

    const prevGame = state.game
    setState(s => ({ ...s, game: optimisticGame, waiting: true, error: null, lastComment: null }))

    try {
      const res = await api.makeMove(state.gameId, uci)
      const gameData = await api.getGame(state.gameId)

      const game = new Chess()
      for (const m of gameData.moves) game.move(m.san)

      const evalHistory = [...state.evalHistory]
      const playerPly = gameData.moves.length - (res.ai_move ? 1 : 0)
      if (res.eval_cp != null) evalHistory.push({ ply: playerPly, cp: res.eval_cp })
      if (res.ai_move?.eval_cp != null) evalHistory.push({ ply: gameData.moves.length, cp: res.ai_move.eval_cp })

      setState(s => ({
        ...s,
        game,
        gameData,
        moves: gameData.moves,
        status: res.status,
        waiting: false,
        lastComment: res.ai_move?.comment ?? null,
        evalHistory,
      }))
    } catch (e) {
      setState(s => ({ ...s, game: prevGame, waiting: false, error: String(e) }))
    }
  }, [state.gameId, state.waiting, state.game, state.evalHistory])

  const reset = useCallback(() => {
    setState({
      gameId: null,
      game: new Chess(),
      gameData: null,
      moves: [],
      status: 'idle',
      waiting: false,
      error: null,
      lastComment: null,
      evalHistory: [],
    })
  }, [])

  return { state, startGame, makeMove, reset }
}
