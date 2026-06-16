import { create } from 'zustand'
import type { Cell } from '@/types/api'

interface UIState {
  formOpen: boolean
  selectedCell: Cell | null
  converterCoords: { x: number; y: number; z: number } | null
}

interface UIActions {
  setFormOpen: (open: boolean) => void
  setSelectedCell: (cell: Cell | null) => void
  setConverterCoords: (coords: { x: number; y: number; z: number } | null) => void
}

export const useUIStore = create<UIState & UIActions>()((set) => ({
  formOpen: false,
  selectedCell: null,
  converterCoords: null,
  setFormOpen: (open) => set({ formOpen: open }),
  setSelectedCell: (cell) => set({ selectedCell: cell }),
  setConverterCoords: (coords) => set({ converterCoords: coords }),
}))
