import { client } from '@/api/client'
import { WAREHOUSE_ID } from '@/config'
import type { Cell } from '@/types/api'

export function getAvailableCells(): Promise<{ data: Cell[] | null; error: string | null }> {
  return client<Cell[]>(`/warehouse/${WAREHOUSE_ID}/cells/?available=true`)
}
