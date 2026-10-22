import { useState, useEffect } from 'react'
import type { AnyLogicState } from '@/types/api'

export function useAnyLogicStream(): AnyLogicState | null {
  const [state, setState] = useState<AnyLogicState | null>(null)

  useEffect(() => {
    const es = new EventSource('/api/anylogic/stream')

    es.onmessage = (event: MessageEvent<string>) => {
      try {
        const data: AnyLogicState | null = JSON.parse(event.data) as AnyLogicState | null
        if (data !== null) setState(data)
      } catch {
        // ignore parse errors
      }
    }

    return () => es.close()
  }, [])

  return state
}
