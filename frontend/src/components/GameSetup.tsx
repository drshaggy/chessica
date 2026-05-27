import { useState, useEffect } from 'react'
import { api } from '../api'
import type { GameSettings } from '../types'

interface Props {
  onStart: (settings: GameSettings) => void
  disabled?: boolean
}

const PRESETS = [
  { label: 'Sicilian Dragon', value: 'Play the Sicilian Dragon as Black. After 1.e4 c5, aim for the Dragon setup with ...g6, ...d6, ...Bg7. Launch a kingside attack.' },
  { label: "King's Indian", value: "Play the King's Indian Defence as Black. Castle kingside early and launch a kingside counterattack." },
  { label: 'Quiet positional', value: 'Play quiet, positional chess. Favour piece activity, pawn structure, and long-term strategic advantages over tactics.' },
  { label: 'Sharp tactical', value: 'Play sharp, tactical chess. Look for sacrifices, combinations, and dynamic piece play.' },
  { label: 'Endgame practise', value: 'Exchange pieces early and steer the game toward an endgame. Play technically precise endgame chess.' },
  { label: 'Puzzle style', value: 'Create complex tactical positions with lots of pins, forks, and mating threats so the human can practise calculation.' },
]

export default function GameSetup({ onStart, disabled }: Props) {
  const [levels, setLevels] = useState<string[]>([])
  const [color, setColor] = useState<'white' | 'black' | 'random'>('white')
  const [level, setLevel] = useState('master')
  const [style, setStyle] = useState('')

  useEffect(() => {
    api.getLevels().then(setLevels).catch(() => {})
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStart({ player_color: color, stockfish_level: level, style_prompt: style || 'Play natural, principled chess.' })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Play as</label>
        <div className="flex gap-2">
          {(['white', 'black', 'random'] as const).map(c => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              className={`flex-1 py-2 px-3 rounded text-sm font-medium border transition-colors ${
                color === c
                  ? 'bg-amber-500 border-amber-500 text-gray-900'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-500'
              }`}
            >
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">AI Strength</label>
        <select
          value={level}
          onChange={e => setLevel(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-amber-500"
        >
          {(levels.length ? levels : ['beginner','novice','intermediate','club','expert','master','grandmaster','max']).map(l => (
            <option key={l} value={l}>
              {l.charAt(0).toUpperCase() + l.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Style / Instructions</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {PRESETS.map(p => (
            <button
              key={p.label}
              type="button"
              onClick={() => setStyle(p.value)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${
                style === p.value
                  ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        <textarea
          value={style}
          onChange={e => setStyle(e.target.value)}
          placeholder="Describe the opening, style, or scenario you want to practise..."
          rows={3}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-amber-500 resize-none"
        />
      </div>

      <button
        type="submit"
        disabled={disabled}
        className="w-full py-2.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed text-gray-900 font-semibold rounded transition-colors"
      >
        Start Game
      </button>
    </form>
  )
}
