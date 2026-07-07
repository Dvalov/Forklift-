import { useState, useEffect } from 'react'
import type { Forklift } from '@/types/api'

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':')
}

interface TopStatusBarProps {
  mode: string
  signal: { type: string; strength: number }
  connected: boolean
  taskNumber: string | null
  errorCount: number
  cargoWeight: number
  forkliftStatus?: Forklift['status']
}

const badgeBase: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '5px',
  padding: '3px 10px',
  borderRadius: '6px',
  fontSize: '13px',
  fontWeight: 500,
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(0,255,255,0.18)',
  whiteSpace: 'nowrap',
}

export default function TopStatusBar({ mode, signal, connected, taskNumber, errorCount, cargoWeight, forkliftStatus }: TopStatusBarProps) {
  const [elapsed, setElapsed] = useState(0)
  const frozen = forkliftStatus === 'stopped' || forkliftStatus === 'error'

  useEffect(() => {
    const id = setInterval(() => {
      if (!frozen) setElapsed((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(id)
  }, [frozen])

  return (
    <div
      className="rounded-2xl px-3 py-2"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <div className="flex flex-wrap gap-2 items-center">
        <span style={badgeBase}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: connected ? '#3fb950' : '#ff3366', display: 'inline-block', flexShrink: 0 }} />
          <span style={{ color: '#6a8aaa' }}>Режим</span>
          <span style={{ color: '#e0f0ff', fontWeight: 700 }}>{mode.toUpperCase()}</span>
        </span>

        <span style={badgeBase}>
          <span style={{ color: '#8ab4f8', fontSize: '13px' }}>📶</span>
          <span style={{ color: '#6a8aaa' }}>Связь</span>
          <span style={{ color: '#e0f0ff', fontWeight: 700 }}>{signal.type} ({signal.strength}%)</span>
        </span>

        <span style={badgeBase}>
          <span style={{ color: '#8ab4f8', fontSize: '13px' }}>📋</span>
          <span style={{ color: '#6a8aaa' }}>Задание</span>
          <span style={{ color: '#e0f0ff', fontWeight: 700 }}>{taskNumber ?? '—'}</span>
        </span>

        <span style={{ ...badgeBase, borderColor: 'rgba(0,255,255,0.35)' }}>
          <span style={{ color: '#8ab4f8', fontSize: '13px' }}>⏱</span>
          <span style={{ color: '#6a8aaa' }}>Время работы</span>
          <span style={{ color: '#00ffff', fontFamily: "'Courier New', monospace", fontWeight: 700 }}>{formatUptime(elapsed)}</span>
        </span>

        {errorCount > 0 && (
          <span style={{ ...badgeBase, background: 'rgba(255,170,0,0.1)', borderColor: 'rgba(255,170,0,0.4)' }}>
            <span style={{ fontSize: '13px' }}>⚠️</span>
            <span style={{ color: '#ffaa00', fontWeight: 600 }}>Ошибок {errorCount} (сенсор)</span>
          </span>
        )}

        <span style={badgeBase}>
          <span style={{ fontSize: '13px' }}>📦</span>
          <span style={{ color: '#6a8aaa' }}>Груз</span>
          <span style={{ color: '#e0f0ff', fontWeight: 700 }}>{cargoWeight} кг</span>
        </span>
      </div>
    </div>
  )
}
