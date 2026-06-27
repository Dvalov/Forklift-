import { client } from '@/api/client'
import { WAREHOUSE_ID } from '@/config'
import type { Coordinates } from '@/types/api'

export function convertCellToCoords(
  x: number,
  y: number,
  z: number,
): Promise<{ data: Coordinates | null; error: string | null }> {
  return client<Coordinates>(`/api/converter/${WAREHOUSE_ID}/cells/convert/?x=${x}&y=${y}&z=${z}`)
}
