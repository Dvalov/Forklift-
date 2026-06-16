import { client } from '@/api/client'
import { WAREHOUSE_ID } from '@/config'
import type { Coordinates } from '@/types/api'

export function convertCellToCoords(
  x: number,
  y: number,
  z: number,
): Promise<{ data: Coordinates | null; error: string | null }> {
  return client<Coordinates>(`/converter/${WAREHOUSE_ID}/?x=${x}&y=${y}&z=${z}`)
}
