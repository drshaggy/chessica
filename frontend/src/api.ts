import type { GameState, GameSettings, Analysis } from './types'

const BASE = '/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export const api = {
  getLevels: () => req<string[]>('/levels'),

  createGame: (settings: GameSettings) =>
    req<{ game_id: string; player_color: string; initial_ai_move: unknown }>(
      '/games',
      { method: 'POST', body: JSON.stringify(settings) }
    ),

  getGame: (id: string) => req<GameState>(`/games/${id}`),

  listGames: () => req<{ id: string; created_at: string; settings: GameSettings; status: string }[]>('/games'),

  makeMove: (id: string, uci: string) =>
    req<{
      san: string
      fen: string
      status: string
      eval_cp: number | null
      ai_move: { san: string; uci: string; comment: string | null; eval_cp: number | null } | null
      book_moves: { uci: string; san: string; weight: number }[]
      tablebase: unknown | null
    }>(`/games/${id}/move`, { method: 'POST', body: JSON.stringify({ uci }) }),

  requestAnalysis: (id: string) =>
    req<{ status: string; analysis?: Analysis }>(`/games/${id}/analyze`, { method: 'POST' }),

  getAnalysis: (id: string) =>
    req<{ status: string; analysis?: Analysis }>(`/games/${id}/analysis`),

  chat: (id: string, message: string) =>
    req<{ response: string }>(`/games/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
}
