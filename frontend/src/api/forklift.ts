import { client } from '@/api/client'
import { FORKLIFT_ID } from '@/config'
import type { Forklift } from '@/types/api'

export function getForklift(): Promise<{ data: Forklift | null; error: string | null }> {
  return client<Forklift>(`/api/forklifts/${FORKLIFT_ID}/`)
}

export function updateForkliftCellPosition(
  id: string,
  cellX: number,
  cellZ: number,
): Promise<{ data: Forklift | null; error: string | null }> {
  return client<Forklift>(`/api/forklifts/${id}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cell_x: cellX, cell_z: cellZ }),
  })
}
