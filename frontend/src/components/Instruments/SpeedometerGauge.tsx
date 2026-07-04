interface SpeedometerGaugeProps {
  speed: number
  maxSpeed: number
  direction: 'forward' | 'backward' | 'stop'
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

function zoneLabel(speed: number, maxSpeed: number): string {
  const pct = speed / maxSpeed
  if (pct < 0.4) return 'Малая скорость'
  if (pct < 0.7) return 'Средняя скорость'
  return 'Высокая скорость'
}

export default function SpeedometerGauge({ speed, maxSpeed, direction }: SpeedometerGaugeProps) {
  const directions = [
    { key: 'forward', label: '▶ Вперёд' },
    { key: 'stop', label: '■ Стоп' },
    { key: 'backward', label: '◀ Назад' },
  ]

  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <svg viewBox="0 0 200 200" style={{ width: '100%', height: 'auto', display: 'block' }}>
        {/* Background arc track */}
        <path
          d={arcPath(100, 110, 70, -140, 140)}
          stroke="rgba(0,255,255,0.2)"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
        />

        {/* Zone arcs */}
        <path d={arcPath(100, 110, 58, -140, -28)} stroke="#3fb950" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d={arcPath(100, 110, 58, -28, 56)} stroke="#ffaa00" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d={arcPath(100, 110, 58, 56, 140)} stroke="#ff3366" strokeWidth="3" fill="none" strokeLinecap="round" />

        {/* Needle */}
        <line
          x1="100" y1="110" x2="100" y2="45"
          stroke="#00ffff"
          strokeWidth="3"
          strokeLinecap="round"
          style={{
            transform: `rotate(${speedToAngle(speed, maxSpeed)}deg)`,
            transformOrigin: '100px 110px',
          }}
        />

        {/* Pivot circle */}
        <circle cx="100" cy="110" r="5" fill="#00ffff" />

        {/* Digital speed */}
        <text
          x="100" y="158"
          textAnchor="middle"
          fill="#00ffff"
          fontFamily="'Courier New', monospace"
          fontSize="24"
          fontWeight="600"
        >
          {speed.toFixed(1)}
        </text>

        {/* Unit label */}
        <text x="100" y="176" textAnchor="middle" fill="#6a8aaa" fontSize="12">
          м/с
        </text>
      </svg>

      {/* Direction indicators */}
      <div className="flex justify-center gap-2 mt-3">
        {directions.map(({ key, label }) => (
          <span
            key={key}
            className="px-3 py-1 rounded text-sm"
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

      {/* Zone label */}
      <p className="text-center mt-2" style={{ color: '#6a8aaa', fontSize: '12px' }}>
        {zoneLabel(speed, maxSpeed)}
      </p>
    </div>
  )
}
