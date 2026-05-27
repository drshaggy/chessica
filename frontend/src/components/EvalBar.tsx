interface Props {
  cp: number | null   // centipawns, positive = white winning
  orientation: 'white' | 'black'
}

function cpToPercent(cp: number | null): number {
  if (cp === null) return 50
  // Sigmoid-like mapping: 0 cp = 50%, ±500 = ~75/25%, ±1000 = ~90/10%
  return 50 + 50 * (2 / (1 + Math.exp(-cp / 400)) - 1)
}

function cpToLabel(cp: number | null): string {
  if (cp === null) return '—'
  const abs = Math.abs(cp)
  if (abs >= 10000) {
    const mate = Math.ceil((10000 - abs) / 2)
    return `M${mate}`
  }
  return (cp / 100).toFixed(1)
}

export default function EvalBar({ cp, orientation }: Props) {
  const whitePct = cpToPercent(cp)
  const label = cpToLabel(cp)

  return (
    <div className="flex flex-col items-center w-6 gap-1">
      <span className="text-xs text-gray-400 font-mono">{label}</span>
      <div className="flex-1 w-full rounded overflow-hidden bg-gray-900 relative" style={{ minHeight: 300 }}>
        {/* White section */}
        <div
          className="absolute bottom-0 left-0 right-0 bg-gray-100 transition-all duration-300"
          style={{ height: `${whitePct}%` }}
        />
        {/* Black section fills the rest from top */}
      </div>
    </div>
  )
}
