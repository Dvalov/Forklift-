import { client } from '@/api/client'
import type { AnyLogicState } from '@/types/api'

export function getAnyLogicState(): Promise<{ data: AnyLogicState | null; error: string | null }> {
  return client<AnyLogicState>('/api/anylogic/state')
}

export async function postAnyLogicOrder(sourceCellId: number, destCellId: number): Promise<void> {
  const { error } = await client<{ ok: boolean }>('/api/anylogic/order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sourceCellId, destCellId }),
  })
  if (error !== null) {
    console.warn('[AnyLogic] order failed:', error)
  }
}
