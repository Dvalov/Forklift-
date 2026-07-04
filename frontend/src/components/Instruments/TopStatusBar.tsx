import { useState, useEffect } from 'react'

interface TopStatusBarProps {
  mode: string
  connected: boolean
  taskNumber: string | null
  errorText: string | null
  cargoWeight: number
}

export default function TopStatusBar({ mode, connected, taskNumber, errorText, cargoWeight }: TopStatusBarProps) {
  const [clock, setClock] = useState(() => new Date().toLocaleTimeString('ru-RU'))

  useEffect(() => {
    const id = setInterval(() => setClock(new Date().toLocaleTimeString('ru-RU')), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-1">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Режим:</span>
          <span style={{ color: '#e0f0ff', fontSize: '12px', fontWeight: 600 }}>{mode}</span>
        </div>

        <div className="flex items-center gap-1">
          <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: connected ? '#00ffff' : '#ff3366' }} />
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Связь</span>
        </div>

        <div className="flex items-center gap-1">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Задание:</span>
          <span style={{ color: '#e0f0ff', fontSize: '12px', fontWeight: 600 }}>{taskNumber ?? '—'}</span>
        </div>

        {errorText !== null && (
          <span style={{ color: '#ff3366', fontSize: '12px' }}>{errorText}</span>
        )}

        <div className="flex items-center gap-1">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Груз:</span>
          <span style={{ color: '#e0f0ff', fontSize: '12px', fontWeight: 600 }}>{cargoWeight} кг</span>
        </div>

        <span style={{ color: '#00ffff', fontFamily: "'Courier New', monospace", fontSize: '24px', fontWeight: 600 }}>
          {clock}
        </span>
      </div>
    </div>
  )
}
