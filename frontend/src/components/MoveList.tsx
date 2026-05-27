import type { MoveRecord } from '../types'

interface Props {
  moves: MoveRecord[]
  currentPly?: number
  onSelectPly?: (ply: number) => void
  lastComment?: string | null
}

const CLASS_SYMBOL: Record<string, string> = {
  blunder: '??',
  mistake: '?',
  inaccuracy: '?!',
}

export default function MoveList({ moves, currentPly, onSelectPly, lastComment }: Props) {
  const pairs: [MoveRecord, MoveRecord | null][] = []
  for (let i = 0; i < moves.length; i += 2) {
    pairs.push([moves[i], moves[i + 1] ?? null])
  }

  return (
    <div className="flex flex-col gap-1 text-sm">
      {pairs.map(([white, black], i) => (
        <div key={i} className="flex gap-1 items-baseline">
          <span className="text-gray-600 w-6 text-right shrink-0">{i + 1}.</span>
          <MoveCell move={white} currentPly={currentPly} onSelect={onSelectPly} />
          {black && <MoveCell move={black} currentPly={currentPly} onSelect={onSelectPly} />}
        </div>
      ))}
      {lastComment && (
        <div className="mt-2 text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded px-2 py-1.5 italic">
          {lastComment}
        </div>
      )}
    </div>
  )
}

function MoveCell({
  move,
  currentPly,
  onSelect,
}: {
  move: MoveRecord
  currentPly?: number
  onSelect?: (ply: number) => void
}) {
  const isActive = currentPly === move.ply
  return (
    <button
      onClick={() => onSelect?.(move.ply)}
      className={`px-1.5 py-0.5 rounded font-mono transition-colors ${
        isActive
          ? 'bg-amber-500 text-gray-900'
          : 'hover:bg-gray-700 text-gray-200'
      }`}
    >
      {move.san}
      {move.is_book ? (
        <span className="text-blue-400 text-xs ml-0.5" title="Book move">♟</span>
      ) : null}
    </button>
  )
}
