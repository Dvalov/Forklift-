import { useState, useEffect } from 'react'
import { useAvailableCells } from './useAvailableCells'
import { useCreateTask } from './useCreateTask'
import { convertCellToCoords } from '@/api/converter'
import { FORKLIFT_ID } from '@/config'
import type { Cell, Coordinates } from '@/types/api'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export default function TaskCreationForm() {
  const { data: cellsResult, isLoading: cellsLoading } = useAvailableCells()
  const createTaskMutation = useCreateTask()
  const cells: Cell[] = cellsResult?.data ?? []

  const [selectedCell, setSelectedCell] = useState<Cell | null>(null)
  const [coords, setCoords] = useState<Coordinates | null>(null)
  const [converterLoading, setConverterLoading] = useState(false)
  const [converterError, setConverterError] = useState<string | null>(null)

  async function runConverter(cell: Cell) {
    setConverterLoading(true)
    setConverterError(null)
    const result = await convertCellToCoords(cell.x, cell.y, cell.z)
    setConverterLoading(false)
    if (result.error) {
      setConverterError(result.error)
      setCoords(null)
    } else {
      setCoords(result.data)
    }
  }

  function handleCellChange(value: string) {
    const cell = cells.find(c => String(c.id) === value) ?? null
    setSelectedCell(cell)
    setCoords(null)
    setConverterError(null)
    if (cell) {
      runConverter(cell)
    }
  }

  function handleRetry() {
    if (selectedCell) {
      runConverter(selectedCell)
    }
  }

  useEffect(() => {
    if (createTaskMutation.isSuccess) {
      setSelectedCell(null)
      setCoords(null)
      setConverterError(null)
      createTaskMutation.reset()
    }
  }, [createTaskMutation.isSuccess, createTaskMutation])

  function handleSubmit() {
    if (!selectedCell || !coords) return
    createTaskMutation.mutate({
      forklift_id: Number(FORKLIFT_ID),
      dest_x: coords.x,
      dest_y: coords.y,
      dest_z: coords.z,
      dest_cell_x: selectedCell.x,
      dest_cell_y: selectedCell.y,
      dest_cell_z: selectedCell.z,
    })
  }

  const isSubmitDisabled =
    !selectedCell || !coords || converterLoading || createTaskMutation.isPending

  const submitLabel =
    converterLoading || createTaskMutation.isPending ? '…' : 'Create Task'

  return (
    <section className="px-6 py-4 border-b border-gray-800">
      <p className="text-xs text-gray-400 mb-2 uppercase tracking-wide">New Task</p>
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <Select
            value={selectedCell ? String(selectedCell.id) : ''}
            onValueChange={handleCellChange}
            disabled={cellsLoading}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={cellsLoading ? 'Loading cells…' : 'Select cell'} />
            </SelectTrigger>
            <SelectContent>
              {cells.map(cell => (
                <SelectItem key={cell.id} value={String(cell.id)}>
                  {cell.x}&middot;{cell.y}&middot;{cell.z}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {converterError !== null && (
            <p className="text-xs text-danger mt-1">
              Could not get coordinates —{' '}
              <button onClick={handleRetry} className="underline">
                Retry
              </button>
            </p>
          )}
        </div>
        <button
          disabled={isSubmitDisabled}
          onClick={handleSubmit}
          className="px-4 py-2 text-sm font-medium rounded-md bg-accent text-surface disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex-shrink-0"
        >
          {submitLabel}
        </button>
      </div>
      {createTaskMutation.isError && (
        <p className="text-xs text-danger mt-2">Failed to create task — try again</p>
      )}
    </section>
  )
}
