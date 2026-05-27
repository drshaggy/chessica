import { useState, useEffect, useCallback, useRef } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'
import { useGame } from './hooks/useGame'
import GameSetup from './components/GameSetup'
import MoveList from './components/MoveList'
import EvalBar from './components/EvalBar'
import Review from './components/Review'
import ChatPanel from './components/ChatPanel'
import type { GameSettings } from './types'
import type { Highlights } from './utils/parseHighlights'

type Tab = 'game' | 'review'

const DESKTOP_BOARD = 520
const EVAL_WIDTH = 24 + 8   // w-6 + gap-2
const MOVES_WIDTH = 288
const COL_GAP = 24
const CHAT_HEIGHT = 280

export default function App() {
  const { state, startGame, makeMove, reset } = useGame()
  const [tab, setTab] = useState<Tab>('game')

  const [winW, setWinW] = useState(() => window.innerWidth)
  const [highlights, setHighlights] = useState<Highlights>({ arrows: [], squares: [] })
  const onHover = useCallback((h: Highlights | null) => setHighlights(h ?? { arrows: [], squares: [] }), [])
  const [chatHeight, setChatHeight] = useState(CHAT_HEIGHT)
  const dragState = useRef<{ startY: number; startH: number } | null>(null)

  useEffect(() => {
    const onResize = () => setWinW(window.innerWidth)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const onDragHandleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragState.current = { startY: e.clientY, startH: chatHeight }
    const onMove = (e: MouseEvent) => {
      if (!dragState.current) return
      const delta = dragState.current.startY - e.clientY // drag up = grow
      setChatHeight(Math.max(140, Math.min(600, dragState.current.startH + delta)))
    }
    const onUp = () => {
      dragState.current = null
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [chatHeight])

  // On mobile: board fills screen minus p-4 padding (32px) minus eval bar
  const isMobile = winW < 768
  const boardWidth = isMobile ? Math.max(260, winW - 32 - EVAL_WIDTH) : DESKTOP_BOARD
  const movesWidth = isMobile ? boardWidth + EVAL_WIDTH : MOVES_WIDTH
  const movesHeight = isMobile ? 180 : boardWidth
  const chatWidth = isMobile ? boardWidth + EVAL_WIDTH : DESKTOP_BOARD + COL_GAP + MOVES_WIDTH
  const chatMarginLeft = isMobile ? 0 : EVAL_WIDTH

  const isActive = state.status === 'active'
  const isOver = ['white_won', 'black_won', 'draw'].includes(state.status)
  const playerColor = state.gameData?.settings.player_color as 'white' | 'black' | undefined
  const orientation = playerColor === 'black' ? 'black' : 'white'

  const currentEval = state.evalHistory.length > 0
    ? state.evalHistory[state.evalHistory.length - 1].cp
    : null

  function onDrop(sourceSquare: string, targetSquare: string, piece: string) {
    if (!isActive || state.waiting) return false
    const legalMoves = state.gameData?.legal_moves ?? []
    const testGame = new Chess(state.game.fen())
    const move = testGame.move({ from: sourceSquare, to: targetSquare, promotion: 'q' })
    if (!move) return false
    const uci = sourceSquare + targetSquare + (move.promotion ?? '')
    if (!legalMoves.includes(uci) && !legalMoves.includes(sourceSquare + targetSquare)) return false
    makeMove(uci)
    return true
  }

  const statusLabel = () => {
    if (state.status === 'white_won') return '♔ White wins'
    if (state.status === 'black_won') return '♚ Black wins'
    if (state.status === 'draw') return '½–½ Draw'
    return ''
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <h1 className="text-lg font-bold tracking-tight text-amber-400">Chess AI</h1>
        {state.gameId && (
          <div className="flex gap-2">
            <button onClick={() => setTab('game')}
              className={`px-3 py-1 rounded text-sm ${tab === 'game' ? 'bg-amber-500 text-gray-900' : 'text-gray-400 hover:text-gray-200'}`}>
              Game
            </button>
            <button onClick={() => setTab('review')} disabled={!isOver}
              className={`px-3 py-1 rounded text-sm disabled:opacity-40 ${tab === 'review' ? 'bg-amber-500 text-gray-900' : 'text-gray-400 hover:text-gray-200'}`}>
              Review
            </button>
            <button onClick={() => { reset(); setTab('game') }}
              className="px-3 py-1 rounded text-sm text-gray-500 hover:text-gray-300">
              New
            </button>
          </div>
        )}
      </header>

      <main className="flex-1 flex items-start justify-center p-4 md:p-6">
        {tab === 'review' && state.gameId && state.gameData ? (
          <div className="w-full max-w-3xl">
            <Review gameId={state.gameId} pgn={state.gameData.pgn} />
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            {/* Top row: eval bar + board, then moves panel (side-by-side on desktop, stacked on mobile) */}
            <div className={isMobile ? 'flex flex-col gap-4' : 'flex gap-6 items-start'}>
              {/* Eval bar + board */}
              <div className="flex gap-2 items-start">
                <EvalBar cp={currentEval} orientation={orientation} />
                <div className="relative">
                  <Chessboard
                    position={state.game.fen()}
                    onPieceDrop={onDrop}
                    boardOrientation={orientation}
                    boardWidth={boardWidth}
                    arePiecesDraggable={isActive && !state.waiting}
                    customBoardStyle={{ borderRadius: '6px', boxShadow: '0 4px 24px rgba(0,0,0,0.5)' }}
                    customLightSquareStyle={{ backgroundColor: '#f0d9b5' }}
                    customDarkSquareStyle={{ backgroundColor: '#b58863' }}
                    customArrows={highlights.arrows.map(([f, t]) => [f, t, 'rgba(96,165,250,0.85)'] as [string, string, string])}
                    customSquareStyles={Object.fromEntries(
                      highlights.squares.map(sq => [sq, { backgroundColor: 'rgba(96,165,250,0.25)' }])
                    )}
                  />
                  {state.waiting && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30 rounded">
                      <span className="text-amber-400 text-sm font-medium animate-pulse">Thinking…</span>
                    </div>
                  )}
                  {isOver && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded">
                      <div className="bg-gray-900 border border-gray-700 rounded-lg px-6 py-4 text-center">
                        <div className="text-xl font-bold text-amber-400 mb-2">{statusLabel()}</div>
                        <button onClick={() => setTab('review')}
                          className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-gray-900 font-semibold rounded text-sm mr-2">
                          Review
                        </button>
                        <button onClick={reset}
                          className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm">
                          New game
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Moves / game info panel */}
              <div style={{ width: movesWidth, height: movesHeight }} className="flex flex-col">
                {!state.gameId ? (
                  <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                    <h2 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide">New Game</h2>
                    <GameSetup onStart={startGame} disabled={state.waiting} />
                  </div>
                ) : (
                  <>
                    {/* Game info */}
                    <div className="bg-gray-900 rounded-lg p-3 border border-gray-800 shrink-0 mb-2">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>Level: <span className="text-gray-300">{state.gameData?.settings.stockfish_level}</span></span>
                        <span>You: <span className="text-gray-300">{playerColor}</span></span>
                      </div>
                      {state.gameData?.agent_state?.book_line && (
                        <div className="text-xs text-blue-400 truncate">
                          {state.gameData.agent_state.book_line as string}
                        </div>
                      )}
                      {state.gameData?.agent_state?.plan && (
                        <div className="text-xs text-gray-500 italic mt-0.5 truncate"
                          title={state.gameData.agent_state.plan as string}>
                          {state.gameData.agent_state.plan as string}
                        </div>
                      )}
                      {state.error && <div className="text-xs text-red-400 mt-1">{state.error}</div>}
                      {state.gameData?.book_moves && state.gameData.book_moves.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {state.gameData.book_moves.map(m => (
                            <button key={m.uci}
                              onClick={() => isActive && !state.waiting && makeMove(m.uci)}
                              className="text-xs px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/30 text-blue-300 rounded hover:bg-blue-500/20 font-mono">
                              {m.san}
                            </button>
                          ))}
                        </div>
                      )}
                      {state.gameData?.tablebase && (
                        <div className="mt-2 flex items-center flex-wrap gap-1">
                          <span className={`text-xs font-semibold ${
                            state.gameData.tablebase.wdl === 'win' ? 'text-green-400' :
                            state.gameData.tablebase.wdl === 'loss' ? 'text-red-400' : 'text-gray-400'}`}>
                            TB: {state.gameData.tablebase.wdl.toUpperCase()}
                            {state.gameData.tablebase.dtz != null && ` DTZ${state.gameData.tablebase.dtz}`}
                          </span>
                          {state.gameData.tablebase.moves.slice(0, 3).map(m => (
                            <button key={m.uci}
                              onClick={() => isActive && !state.waiting && makeMove(m.uci)}
                              className={`text-xs px-1.5 py-0.5 border rounded font-mono ${
                                m.wdl === 'win' ? 'bg-green-500/10 border-green-500/30 text-green-300' :
                                m.wdl === 'loss' ? 'bg-red-500/10 border-red-500/30 text-red-300' :
                                'bg-gray-800 border-gray-700 text-gray-400'}`}>
                              {m.san}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Move list */}
                    <div className="bg-gray-900 rounded-lg border border-gray-800 flex-1 overflow-y-auto p-3 min-h-0">
                      <MoveList moves={state.moves} lastComment={state.lastComment} />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Chat row */}
            {state.gameId && (
              <div style={{ marginLeft: chatMarginLeft, width: chatWidth }}>
                {/* Drag handle */}
                <div
                  onMouseDown={onDragHandleMouseDown}
                  className="flex items-center justify-center h-3 cursor-ns-resize group mb-1 select-none"
                >
                  <div className="w-10 h-1 rounded-full bg-gray-700 group-hover:bg-amber-500 transition-colors" />
                </div>
                <div
                  className="bg-gray-900 border border-gray-800 rounded-lg flex flex-col overflow-hidden"
                  style={{ height: chatHeight }}
                >
                  <div className="px-3 py-2 border-b border-gray-800 shrink-0">
                    <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">Chat with AI</span>
                  </div>
                  <ChatPanel gameId={state.gameId} fen={state.game.fen()} onHover={onHover} />
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
