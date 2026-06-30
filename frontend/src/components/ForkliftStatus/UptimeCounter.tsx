import { useState, useEffect } from 'react'
import type { Forklift } from '@/types/api'

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':')
}

export default function UptimeCounter({ status }: { status: Forklift['status'] }) {
  const [elapsed, setElapsed] = useState(0)
  const frozen = status === 'stopped' || status === 'error'

  useEffect(() => {
    const id = setInterval(() => {
      if (!frozen) setElapsed((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(id)
  }, [frozen])

  return (
    <span style={{ color: '#00ffff', fontFamily: "'Courier New', monospace", fontSize: '14px', fontWeight: 600 }}>
      {formatUptime(elapsed)}
    </span>
  )
}
