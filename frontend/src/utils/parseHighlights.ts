import { Chess } from 'chess.js'

export interface Highlights {
  arrows: [string, string][]
  squares: string[]
}

const SAN_RE = /(?<![a-zA-Z])(O-O-O|O-O|[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h](?:x[a-h])?[1-8](?:=[QRBN])?)[+#]?(?![a-zA-Z0-9])/g

function coordsToSquare(file: number, rank: number): string {
  return String.fromCharCode(97 + file) + (rank + 1)
}

// Can this piece type reach `to` from `from` in one move (ignoring blocking)?
function canReach(type: string, fromFile: number, fromRank: number, toFile: number, toRank: number): boolean {
  const df = Math.abs(toFile - fromFile)
  const dr = Math.abs(toRank - fromRank)
  switch (type) {
    case 'n': return (df === 1 && dr === 2) || (df === 2 && dr === 1)
    case 'b': return df === dr && df > 0
    case 'r': return (df === 0 || dr === 0) && df + dr > 0
    case 'q': return (df === dr || df === 0 || dr === 0) && df + dr > 0
    case 'k': return df <= 1 && dr <= 1 && df + dr > 0
    default:  return false
  }
}

// Try to find a source square for the SAN move by scanning the board
function inferSource(san: string, fen: string): string | null {
  const chess = new Chess(fen)
  const destMatch = san.match(/([a-h][1-8])[=+#]?$/)
  if (!destMatch) return null
  const dest = destMatch[1]
  const toFile = dest.charCodeAt(0) - 97
  const toRank = parseInt(dest[1]) - 1

  const firstChar = san[0]

  if (firstChar >= 'A' && firstChar <= 'Z') {
    // Piece move — scan board for matching piece type that can geometrically reach dest
    const pieceType = firstChar.toLowerCase()
    const board = chess.board()
    const candidates: string[] = []

    for (let r = 0; r < 8; r++) {
      for (let f = 0; f < 8; f++) {
        const piece = board[r][f]
        if (piece && piece.type === pieceType) {
          const rank = 7 - r
          if (f === toFile && rank === toRank) continue // same square
          if (canReach(pieceType, f, rank, toFile, toRank)) {
            candidates.push(coordsToSquare(f, rank))
          }
        }
      }
    }

    if (candidates.length === 0) return null
    if (candidates.length === 1) return candidates[0]

    // Disambiguation hint in SAN (e.g. Nbd2, R1e1)
    const disambig = san.slice(1).replace(/x?[a-h][1-8].*$/, '')
    if (disambig) {
      const filtered = candidates.filter(sq => sq.includes(disambig))
      if (filtered.length > 0) return filtered[0]
    }
    return candidates[0]
  } else {
    // Pawn move — source file is san[0], look for pawn nearby
    const srcFile = firstChar
    const destFile = dest[0]
    const destRank = parseInt(dest[1])

    if (srcFile !== destFile) {
      // Capture: pawn on srcFile one rank away
      for (const dr of [1, -1]) {
        const sq = srcFile + (destRank + dr)
        const piece = chess.get(sq as any)
        if (piece && piece.type === 'p') return sq
      }
    } else {
      // Push: pawn 1 or 2 squares away on same file
      for (const dr of [1, -1, 2, -2]) {
        const r = destRank + dr
        if (r < 1 || r > 8) continue
        const sq = destFile + r
        const piece = chess.get(sq as any)
        if (piece && piece.type === 'p') return sq
      }
    }
    return null
  }
}

// Try the move with both turn colours so we catch opponent moves too
function tryMove(san: string, fen: string) {
  for (const turn of ['same', 'swap']) {
    try {
      let f = fen
      if (turn === 'swap') {
        const parts = f.split(' ')
        parts[1] = parts[1] === 'w' ? 'b' : 'w'
        parts[3] = '-'
        f = parts.join(' ')
      }
      const move = new Chess(f).move(san)
      if (move) return move
    } catch {}
  }
  return null
}

export function parseHighlights(text: string, fen: string): Highlights {
  const arrows: [string, string][] = []
  const arrowSquares = new Set<string>()
  const squareHighlights = new Set<string>()

  const addArrow = (from: string, to: string) => {
    if (!arrows.some(([f, t]) => f === from && t === to)) {
      arrows.push([from, to])
      arrowSquares.add(from)
      arrowSquares.add(to)
    }
  }

  for (const match of text.matchAll(SAN_RE)) {
    const san = match[1]

    // 1. Try chess.js validation (correct from/to, handles en passant, castling, etc.)
    const move = tryMove(san, fen)
    if (move) {
      addArrow(move.from, move.to)
      continue
    }

    // 2. Fallback: geometric inference from board state
    if (!san.startsWith('O-O')) {
      const destMatch = san.match(/([a-h][1-8])[=+#]?$/)
      const dest = destMatch?.[1]
      if (dest) {
        const src = inferSource(san, fen)
        if (src) addArrow(src, dest)
        else squareHighlights.add(dest) // last resort: at least highlight the square
      }
    }
  }

  // Standalone square mentions not already covered by an arrow
  for (const m of text.matchAll(/(?<![a-zA-Z])([a-h][1-8])(?![a-zA-Z0-9])/g)) {
    const sq = m[1]
    if (!arrowSquares.has(sq)) squareHighlights.add(sq)
  }

  return { arrows, squares: Array.from(squareHighlights) }
}
