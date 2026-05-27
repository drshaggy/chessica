export interface GameSettings {
  player_color: 'white' | 'black' | 'random'
  stockfish_level: string
  style_prompt: string
}

export interface MoveRecord {
  id: number
  game_id: string
  ply: number
  san: string
  uci: string
  fen_after: string
  eval_cp: number | null
  best_uci: string | null
  is_book: number
  comment: string | null
}

export interface BookMove {
  uci: string
  san: string
  weight: number
}

export interface TablebaseResult {
  wdl: string
  wdl_raw: number
  dtz: number | null
  dtm?: number | null
  moves: { uci: string; san: string; wdl: string; dtz?: number | null }[]
  source: string
}

export interface AiMove {
  san: string
  uci: string
  comment: string | null
  eval_cp: number | null
}

export interface GameState {
  id: string
  created_at: string
  settings: GameSettings
  pgn: string
  status: string
  agent_state: Record<string, unknown>
  moves: MoveRecord[]
  fen: string
  book_moves: BookMove[]
  tablebase: TablebaseResult | null
  legal_moves: string[]
}

export interface MoveAnalysis {
  ply: number
  san: string
  uci: string
  score_before: number
  score_after: number
  delta_cp: number
  classification: 'good' | 'inaccuracy' | 'mistake' | 'blunder'
  best_uci: string | null
  is_book: boolean
  tablebase: TablebaseResult | null
}

export interface Analysis {
  opening_eco: string | null
  opening_name: string | null
  book_depth: number
  narrative: string
  moves: MoveAnalysis[]
}
