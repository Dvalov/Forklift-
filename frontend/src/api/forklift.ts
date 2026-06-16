import { client } from '@/api/client'
import { FORKLIFT_ID } from '@/config'
import type { Forklift } from '@/types/api'

export function getForklift(): Promise<{ data: Forklift | null; error: string | null }> {
  return client<Forklift>(`/api/forklifts/${FORKLIFT_ID}/`)
}
