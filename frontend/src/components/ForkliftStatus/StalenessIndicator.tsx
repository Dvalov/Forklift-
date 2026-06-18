import { useState, useEffect } from 'react'

export default function StalenessIndicator({ lastSuccessAt }: { lastSuccessAt: number | null }) {
  const [ageMs, setAgeMs] = useState<number | null>(null)

  useEffect(() => {
    if (lastSuccessAt === null) return
    const id = setInterval(() => {
      setAgeMs(Date.now() - lastSuccessAt)
    }, 1000)
    setAgeMs(Date.now() - lastSuccessAt)
    return () => clearInterval(id)
  }, [lastSuccessAt])

  if (lastSuccessAt === null || ageMs === null || ageMs < 10_000) return null

  if (ageMs >= 30_000) {
    return (
      <span className="text-danger text-xs animate-pulse">Connection lost</span>
    )
  }

  return (
    <span className="text-warning text-xs">
      Last updated {Math.floor(ageMs / 1000)}s ago
    </span>
  )
}
