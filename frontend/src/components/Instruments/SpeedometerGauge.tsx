interface SpeedometerGaugeProps {
  speed: number
  maxSpeed: number
  direction: 'forward' | 'backward' | 'stop'
  speedAlert?: string | null
}

function speedToAngle(speed: number, maxSpeed: number): number {
  const clamped = Math.max(0, Math.min(speed, maxSpeed))
  return -140 + (clamped / maxSpeed) * 280
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = (angleDeg - 90) * (Math.PI / 180)
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number): string {
  const start = polarToCartesian(cx, cy, r, startDeg)
  const end = polarToCartesian(cx, cy, r, endDeg)
  const largeArc = endDeg - startDeg > 180 ? 1 : 0
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`
}

export default function SpeedometerGauge({ speed, maxSpeed, direction, speedAlert }: SpeedometerGaugeProps) {
  const directions = [
    { key: 'forward', label: '▶ Вперёд' },
    { key: 'stop', label: '■ Стоп' },
    { key: 'backward', label: '◀ Назад' },
  ]

  const tickCount = 7
  const ticks = Array.from({ length: tickCount }, (_, i) => (i * maxSpeed) / (tickCount - 1))

  return (
    <div
      className="rounded-2xl p-3 flex-1 min-h-0 flex flex-col"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      {/* Direction buttons */}
      <div className="flex justify-center gap-2 mb-1 flex-shrink-0">
        {directions.map(({ key, label }) => (
          <span
            key={key}
            className="px-2 py-0.5 rounded text-xs"
            style={
              direction === key
                ? { background: 'rgba(0,255,255,0.15)', color: '#00ffff', border: '1px solid rgba(0,255,255,0.4)', fontWeight: 600 }
                : { background: 'rgba(0,0,0,0.3)', color: '#6a8aaa', border: '1px solid rgba(106,138,170,0.3)' }
            }
          >
            {label}
          </span>
        ))}
      </div>

      {/* Speed alert */}
      {speedAlert && (
        <p className="text-center text-xs mb-1 flex-shrink-0" style={{ color: '#ff3366', fontWeight: 700 }}>
          ⚠ {speedAlert.toUpperCase()}
        </p>
      )}

      {/* SVG gauge — fills all remaining space */}
      <div className="flex-1 min-h-0 relative">
        <svg
          viewBox="0 0 200 175"
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Background arc */}
          <path
            d={arcPath(100, 100, 70, -140, 140)}
            stroke="rgba(0,255,255,0.2)"
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
          />

          {/* Zone arcs */}
          <path d={arcPath(100, 100, 58, -140, -28)} stroke="#3fb950" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d={arcPath(100, 100, 58, -28, 56)} stroke="#ffaa00" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d={arcPath(100, 100, 58, 56, 140)} stroke="#ff3366" strokeWidth="3" fill="none" strokeLinecap="round" />

          {/* Tick marks and labels */}
          {ticks.map((tickSpeed, i) => {
            const angle = speedToAngle(tickSpeed, maxSpeed)
            const outer = polarToCartesian(100, 100, 76, angle)
            const inner = polarToCartesian(100, 100, 69, angle)
            const lbl = polarToCartesian(100, 100, 86, angle)
            return (
              <g key={i}>
                <line x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} stroke="rgba(0,255,255,0.45)" strokeWidth="1.5" strokeLinecap="round" />
                <text x={lbl.x} y={lbl.y} textAnchor="middle" dominantBaseline="middle" fill="#6a8aaa" fontSize="9">
                  {tickSpeed % 1 === 0 ? tickSpeed.toFixed(0) : tickSpeed.toFixed(1)}
                </text>
              </g>
            )
          })}

          {/* Needle */}
          <line
            x1="100" y1="100" x2="100" y2="38"
            stroke="#00ffff"
            strokeWidth="3"
            strokeLinecap="round"
            style={{ transform: `rotate(${speedToAngle(speed, maxSpeed)}deg)`, transformOrigin: '100px 100px' }}
          />

          {/* Pivot */}
          <circle cx="100" cy="100" r="5" fill="#00ffff" />

          {/* Speed value */}
          <text x="100" y="128" textAnchor="middle" fill="#00ffff" fontFamily="'Courier New', monospace" fontSize="26" fontWeight="600">
            {speed.toFixed(2)}
          </text>
          <text x="100" y="146" textAnchor="middle" fill="#6a8aaa" fontSize="11">
            м/с
          </text>
        </svg>
      </div>
    </div>
  )
}
