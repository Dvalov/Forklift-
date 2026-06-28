import { useState, useEffect, useMemo } from 'react'
import { useAvailableCells } from './useAvailableCells'
import { useCreateTask } from './useCreateTask'
import { useTasksQuery } from '@/components/TaskList/useTasksQuery'
import { convertCellToCoords } from '@/api/converter'
import { FORKLIFT_ID } from '@/config'
import type { Cell, Coordinates } from '@/types/api'
import CellMaskInput from './CellMaskInput'

const DIGIT_SLOTS = 3

function getSuggestions(digits: string, cells: Cell[]): Cell[] {
  if (digits.length === 0) return []
  return cells.filter(cell => {
    if (digits[0] !== undefined && cell.x !== parseInt(digits[0], 10)) return false
    if (digits[1] !== undefined && cell.y !== parseInt(digits[1], 10)) return false
    if (digits[2] !== undefined && cell.z !== parseInt(digits[2], 10)) return false
    return true
  })
}

export default function TaskCreationForm() {
  const { data: cellsResult, isLoading: cellsLoading } = useAvailableCells()
  const { data: tasks } = useTasksQuery()
  const createTaskMutation = useCreateTask()
  const cells: Cell[] = cellsResult?.data ?? []

  const activeCellKeys = useMemo(() => {
    const active = (tasks ?? []).filter(t => t.status === 'pending' || t.status === 'in_progress')
    return new Set(active.map(t => `${t.dest_cell_x},${t.dest_cell_y},${t.dest_cell_z}`))
  }, [tasks])

  const availableCells = useMemo(
    () => cells.filter(c => !activeCellKeys.has(`${c.x},${c.y},${c.z}`)),
    [cells, activeCellKeys],
  )

  const [digits, setDigits] = useState('')
  const [selectedCell, setSelectedCell] = useState<Cell | null>(null)
  const [cellError, setCellError] = useState<string | null>(null)
  const [cellWarn, setCellWarn] = useState<string | null>(null)
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

  function handleDigitsChange(newDigits: string) {
    setDigits(newDigits)
    setSelectedCell(null)
    setCoords(null)
    setCellError(null)
    setCellWarn(null)
    setConverterError(null)

    if (newDigits.length < DIGIT_SLOTS) return

    const [x, y, z] = [
      parseInt(newDigits[0], 10),
      parseInt(newDigits[1], 10),
      parseInt(newDigits[2], 10),
    ]
    const cell = cells.find(c => c.x === x && c.y === y && c.z === z)

    if (!cell) {
      setCellError('Cell not found')
      return
    }

    const cellKey = `${x},${y},${z}`
    if (activeCellKeys.has(cellKey)) {
      const activeTask = (tasks ?? []).find(
        t =>
          (t.status === 'pending' || t.status === 'in_progress') &&
          t.dest_cell_x === x && t.dest_cell_y === y && t.dest_cell_z === z,
      )
      const statusLabel = activeTask?.status === 'in_progress' ? 'in progress' : (activeTask?.status ?? 'active')
      setCellWarn(`Cell is already in tasks with status: ${statusLabel}`)
      return
    }

    if (!cell.available) {
      setCellError('Cell not available')
      return
    }

    setSelectedCell(cell)
    runConverter(cell)
  }

  useEffect(() => {
    if (createTaskMutation.isSuccess) {
      setDigits('')
      setSelectedCell(null)
      setCoords(null)
      setCellError(null)
      setCellWarn(null)
      setConverterError(null)
      createTaskMutation.reset()
    }
  }, [createTaskMutation.isSuccess, createTaskMutation])

  function handleSelectSuggestion(cell: Cell) {
    handleDigitsChange(`${cell.x}${cell.y}${cell.z}`)
  }

  function handleRetry() {
    if (selectedCell) runConverter(selectedCell)
  }

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
          <CellMaskInput
            digits={digits}
            onChange={handleDigitsChange}
            suggestions={getSuggestions(digits, availableCells)}
            onSelectSuggestion={handleSelectSuggestion}
            disabled={cellsLoading || createTaskMutation.isPending}
            hasError={!!cellError}
          />
          {cellWarn !== null && (
            <p className="text-xs text-warning mt-1">{cellWarn}</p>
          )}
          {(cellError !== null || converterError !== null) && (
            <p className="text-xs text-danger mt-1">
              {cellError ?? converterError}
              {converterError !== null && (
                <> —{' '}
                  <button onClick={handleRetry} className="underline">
                    Retry
                  </button>
                </>
              )}
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
