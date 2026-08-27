import { client } from '@/api/client'
import { WAREHOUSE_ID } from '@/config'
import type { Cell } from '@/types/api'

export function getAvailableCells(): Promise<{ data: Cell[] | null; error: string | null }> {
  return client<Cell[]>(`/api/warehouse/${WAREHOUSE_ID}/cells/?available=true`)
}

export function getAllCells(): Promise<{ data: Cell[] | null; error: string | null }> {
  return client<Cell[]>(`/api/warehouse/${WAREHOUSE_ID}/cells/`)
}

export function syncFromOneC(): Promise<{ data: { synced: number; deleted: number } | null; error: string | null }> {
  return client<{ synced: number; deleted: number }>(
    `/api/warehouse/${WAREHOUSE_ID}/sync-from-1c/`,
    { method: 'POST' },
  )
}
