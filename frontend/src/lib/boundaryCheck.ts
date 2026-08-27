import type { Cell, Forklift } from '@/types/api'

const cellDispX = (x: number) => 2 * x - 1

export function checkForkliftBoundary(
  forklift: Forklift,
  cells: Cell[],
): { cellX: number; cellZ: number } | null {
  if (cells.length === 0) return null

  const maxCellX = Math.max(...cells.map(c => c.x))
  const maxCellZ = Math.max(...cells.map(c => c.z))
  const maxDispX = cellDispX(maxCellX)

  // All cell rack positions (display coords), regardless of availability
  const cellPositions = new Set<string>()
  // Only unavailable cell positions — used to trigger the "in occupied cell" check
  const occupiedPositions = new Set<string>()
  for (const c of cells) {
    const key = `${cellDispX(c.x)}:${c.z}`
    cellPositions.add(key)
    if (!c.available) occupiedPositions.add(key)
  }

  const fx = forklift.cell_x
  const fz = forklift.cell_z
  const outOfBounds = fx > maxDispX || fz > maxCellZ || fx < 0 || fz < 0
  const inOccupied = occupiedPositions.has(`${fx}:${fz}`)

  if (!outOfBounds && !inOccupied) return null

  const startX = Math.max(0, Math.min(fx, maxDispX))
  const startZ = Math.max(0, Math.min(fz, maxCellZ))

  // BFS finds nearest position with no cell rack at all (aisle position)
  return bfsNearestFree(startX, startZ, cellPositions, maxDispX, maxCellZ)
}

function bfsNearestFree(
  startX: number,
  startZ: number,
  blocked: Set<string>,
  maxDispX: number,
  maxDispZ: number,
): { cellX: number; cellZ: number } {
  const visited = new Set<string>([`${startX}:${startZ}`])
  const queue: Array<{ x: number; z: number }> = [{ x: startX, z: startZ }]

  while (queue.length > 0) {
    const { x, z } = queue.shift()!
    if (!blocked.has(`${x}:${z}`)) return { cellX: x, cellZ: z }

    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
      const nx = x + dx
      const nz = z + dz
      const nkey = `${nx}:${nz}`
      if (nx >= 0 && nz >= 0 && nx <= maxDispX && nz <= maxDispZ && !visited.has(nkey)) {
        visited.add(nkey)
        queue.push({ x: nx, z: nz })
      }
    }
  }

  return { cellX: 0, cellZ: 0 }
}
