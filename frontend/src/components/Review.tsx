import { useState, useEffect } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { api } from '../api'
import type { Analysis, MoveAnalysis } from '../types'

interface Props {
  gameId: string
  pgn: string
}

const CLASS_COLOR: Record<string, string> = {
  blunder: 'text-red-400',
  mistake: 'text-orange-400',
  inaccuracy: 'text-yellow-400',
  good: 'text-green-400',
}
const CLASS_BG: Record<string, string> = {
  blunder: 'bg-red-500/20 border-red-500/50',
  mistake: 'bg-orange-500/20 border-orange-500/50',
  inaccuracy: 'bg-yellow-500/20 border-yellow-500/50',
  good: 'bg-gray-800 border-gray-700',
}

export default function Review({ gameId, pgn }: Props) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [status, setStatus] = useState<'idle' | 'pending' | 'done' | 'error'>('idle')
  const [selectedPly, setSelectedPly] = useState<number | null>(null)
  const [previewFen, setPreviewFen] = useState<string | null>(null)

  useEffect(() => {
    api.getAnalysis(gameId).then(r => {
      if (r.status === 'done' && r.analysis) {
        setAnalysis(r.analysis)
        setStatus('done')
      } else if (r.status === 'pending') {
        setStatus('pending')
      } else {
        // Auto-start analysis — no extra click needed
        setStatus('pending')
        api.requestAnalysis(gameId)
      }
    })
  }, [gameId])

  useEffect(() => {
    if (status !== 'pending') return
    const iv = setInterval(async () => {
      const r = await api.getAnalysis(gameId)
      if (r.status === 'done' && r.analysis) {
        setAnalysis(r.analysis)
        setStatus('done')
        clearInterval(iv)
      } else if (r.status === 'error') {
        setStatus('error')
        clearInterval(iv)
      }
    }, 3000)
    return () => clearInterval(iv)
  }, [gameId, status])

  const requestAnalysis = async () => {
    setStatus('pending')
    await api.requestAnalysis(gameId)
  }

  const selectMove = (move: MoveAnalysis) => {
    setSelectedPly(move.ply)
    // Reconstruct board at this ply
    const game = new Chess()
    const moves = analysis!.moves.slice(0, move.ply)
    for (const m of moves) game.move(m.san)
    setPreviewFen(game.fen())
  }

  const chartData = analysis?.moves.map(m => ({
    ply: m.ply,
    label: `${Math.ceil(m.ply / 2)}. ${m.san}`,
    cp: Math.max(-1200, Math.min(1200, m.score_after)),
  })) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-100">Game Review</h2>
        {status === 'pending' && (
          <span className="text-sm text-amber-400 animate-pulse">Analysing…</span>
        )}
        {status === 'error' && (
          <button onClick={requestAnalysis} className="text-sm text-red-400 hover:text-red-300">
            Analysis failed — retry
          </button>
        )}
      </div>

      {analysis && (
        <>
          {/* Opening badge */}
          {analysis.opening_name && (
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 rounded px-3 py-1.5">
              <span className="text-xs font-mono text-blue-400">{analysis.opening_eco}</span>
              <span className="text-sm text-blue-300">{analysis.opening_name}</span>
              <span className="text-xs text-gray-500">(book: move {Math.floor(analysis.book_depth / 2)})</span>
            </div>
          )}

          {/* Eval graph */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Evaluation</h3>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={chartData} onClick={d => {
                if (d?.activePayload?.[0]) {
                  const ply = d.activePayload[0].payload.ply
                  const m = analysis.moves.find(x => x.ply === ply)
                  if (m) selectMove(m)
                }
              }}>
                <XAxis dataKey="ply" hide />
                <YAxis domain={[-1200, 1200]} hide />
                <ReferenceLine y={0} stroke="#4b5563" />
                <Tooltip
                  content={({ payload }) => {
                    const d = payload?.[0]?.payload
                    if (!d) return null
                    return (
                      <div className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs">
                        <div className="text-gray-300">{d.label}</div>
                        <div className="text-amber-400">{(d.cp / 100).toFixed(2)}</div>
                      </div>
                    )
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="cp"
                  stroke="#f59e0b"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Side by side: board preview + move list */}
          <div className="flex gap-4">
            {previewFen && (
              <div className="w-48 shrink-0">
                <Chessboard
                  position={previewFen}
                  boardWidth={192}
                  arePiecesDraggable={false}
                  customBoardStyle={{ borderRadius: '6px', boxShadow: '0 2px 8px rgba(0,0,0,0.4)' }}
                />
              </div>
            )}
            <div className="flex-1 max-h-64 overflow-y-auto space-y-1 pr-1">
              {analysis.moves.map(m => (
                <button
                  key={m.ply}
                  onClick={() => selectMove(m)}
                  className={`w-full text-left px-2 py-1 rounded border text-sm transition-colors ${
                    selectedPly === m.ply
                      ? 'ring-1 ring-amber-500'
                      : ''
                  } ${CLASS_BG[m.classification]}`}
                >
                  <span className="text-gray-500 mr-1">{Math.ceil(m.ply / 2)}.</span>
                  <span className="font-mono">{m.san}</span>
                  {m.classification !== 'good' && (
                    <span className={`ml-1 font-bold ${CLASS_COLOR[m.classification]}`}>
                      {m.classification === 'blunder' ? '??' : m.classification === 'mistake' ? '?' : '?!'}
                    </span>
                  )}
                  {m.is_book && <span className="ml-1 text-xs text-blue-400">📖</span>}
                  {m.tablebase && (
                    <span className="ml-1 text-xs text-purple-400">TB:{m.tablebase.wdl}</span>
                  )}
                  <span className="float-right text-xs text-gray-500">
                    {(m.score_after / 100).toFixed(1)}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* AI narrative */}
          <div className="bg-gray-900 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-3">AI Analysis</h3>
            <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
              {analysis.narrative}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
