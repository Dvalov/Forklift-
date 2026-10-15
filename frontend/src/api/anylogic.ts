import { client } from '@/api/client'
import type { AnyLogicState } from '@/types/api'

export function getAnyLogicState(): Promise<{ data: AnyLogicState | null; error: string | null }> {
  return client<AnyLogicState>('/api/anylogic/state')
}
