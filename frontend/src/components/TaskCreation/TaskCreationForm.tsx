import { useState, useEffect, useMemo } from 'react'
import { useAvailableCells } from './useAvailableCells'
import { useCreateTask } from './useCreateTask'
import { useTasksQuery } from '@/components/TaskList/useTasksQuery'
import { convertCellToCoords } from '@/api/converter'
import { FORKLIFT_ID } from '@/config'
import type { Cell, Coordinates } from '@/types/api'
import CellMaskInput from './CellMaskInput'
import { postAnyLogicOrder } from '@/api/anylogic'
import { useAnyLogicQuery } from '@/components/Instruments/useAnyLogicQuery'
import { useAllCellsQuery } from '@/components/Instruments/useAllCellsQuery'

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
  const anylogicState = useAnyLogicQuery()
  const cells: Cell[] = cellsResult?.data ?? []
  const allCells: Cell[] = useAllCellsQuery()

  const activeCellKeys = useMemo(() => {
    const active = (tasks ?? []).filter(t => t.status === 'pending' || t.status === 'in_progress')
    return new Set(active.map(t => `${t.dest_cell_x},${t.dest_cell_y},${t.dest_cell_z}`))
  }, [tasks])

  const availableCells = useMemo(
    () => cells.filter(c => !activeCellKeys.has(`${c.x},${c.y},${c.z}`)),
    [cells, activeCellKeys],
  )

  // Source cell state
  const [sourceDigits, setSourceDigits] = useState('')
  const [sourceCell, setSourceCell] = useState<Cell | null>(null)
  const [sourceCellError, setSourceCellError] = useState<string | null>(null)

  // Dest cell state
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

  function handleSourceDigitsChange(newDigits: string) {
    setSourceDigits(newDigits)
    setSourceCell(null)
    setSourceCellError(null)

    if (newDigits.length < DIGIT_SLOTS) return

    const [x, y, z] = [
      parseInt(newDigits[0], 10),
      parseInt(newDigits[1], 10),
      parseInt(newDigits[2], 10),
    ]
    const cell = allCells.find(c => c.x === x && c.y === y && c.z === z)

    if (!cell) {
      setSourceCellError('Ячейка не найдена')
      return
    }

    setSourceCell(cell)
  }

  function handleSourceSelectSuggestion(cell: Cell) {
    handleSourceDigitsChange(`${cell.x}${cell.y}${cell.z}`)
    setSourceCell(cell)
    setSourceCellError(null)
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
      setCellError('Ячейка не найдена')
      return
    }

    const cellKey = `${x},${y},${z}`
    if (activeCellKeys.has(cellKey)) {
      const activeTask = (tasks ?? []).find(
        t =>
          (t.status === 'pending' || t.status === 'in_progress') &&
          t.dest_cell_x === x && t.dest_cell_y === y && t.dest_cell_z === z,
      )
      const statusLabel = activeTask?.status === 'in_progress' ? 'в работе' : 'ожидает'
      setCellWarn(`Ячейка уже занята задачей: ${statusLabel}`)
      return
    }

    if (!cell.available) {
      setCellError('Ячейка недоступна')
      return
    }

    setSelectedCell(cell)
    runConverter(cell)
  }

  useEffect(() => {
    if (createTaskMutation.isSuccess) {
      if (sourceCell !== null && selectedCell !== null && anylogicState != null && (anylogicState.cells?.length ?? 0) > 0) {
        const alSource = anylogicState.cells.find(c => c.col === sourceCell.x && c.row === sourceCell.z)
        const alDest   = anylogicState.cells.find(c => c.col === selectedCell.x && c.row === selectedCell.z)
        if (alSource !== undefined && alDest !== undefined) {
          void postAnyLogicOrder(alSource.id, alDest.id)
        } else {
          console.warn('[AnyLogic] cell lookup failed', { source: sourceCell, dest: selectedCell })
        }
      }
      setSourceDigits('')
      setSourceCell(null)
      setSourceCellError(null)
      setDigits('')
      setSelectedCell(null)
      setCoords(null)
      setCellError(null)
      setCellWarn(null)
      setConverterError(null)
      createTaskMutation.reset()
    }
  }, [createTaskMutation.isSuccess, createTaskMutation, sourceCell, selectedCell, anylogicState])

  function handleSelectSuggestion(cell: Cell) {
    handleDigitsChange(`${cell.x}${cell.y}${cell.z}`)
  }

  function handleRetry() {
    if (selectedCell) runConverter(selectedCell)
  }

  function handleSubmit() {
    if (!sourceCell || !selectedCell || !coords) return
    createTaskMutation.mutate({
      forklift_id: Number(FORKLIFT_ID),
      dest_x: coords.x,
      dest_y: coords.y,
      dest_z: coords.z,
      dest_cell_x: selectedCell.x,
      dest_cell_y: selectedCell.y,
      dest_cell_z: selectedCell.z,
      source_cell_x: sourceCell.x,
      source_cell_y: sourceCell.y,
      source_cell_z: sourceCell.z,
    })
  }

  const isSubmitDisabled =
    !sourceCell || !selectedCell || !coords || converterLoading || createTaskMutation.isPending

  const submitLabel =
    converterLoading || createTaskMutation.isPending ? '…' : 'Создать задачу'

  return (
    <section
      className="rounded-2xl p-4"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <h2
        className="mb-3"
        style={{
          borderLeft: '3px solid #00ffff',
          paddingLeft: '12px',
          color: '#8ab4f8',
          fontSize: '16px',
          fontWeight: 600,
          lineHeight: 1.2,
        }}
      >
        Новая задача
      </h2>
      <div className="flex flex-col gap-3">
        <div>
          <label style={{ color: '#aaa', fontSize: 13, marginBottom: 4, display: 'block' }}>Откуда</label>
          <CellMaskInput
            digits={sourceDigits}
            onChange={handleSourceDigitsChange}
            suggestions={getSuggestions(sourceDigits, allCells)}
            onSelectSuggestion={handleSourceSelectSuggestion}
            disabled={cellsLoading || createTaskMutation.isPending}
            hasError={!!sourceCellError}
          />
          {sourceCellError && <div style={{ color: '#ff3366', fontSize: 12, marginTop: 4 }}>{sourceCellError}</div>}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <label style={{ color: '#aaa', fontSize: 13, marginBottom: 4, display: 'block' }}>Куда</label>
            <CellMaskInput
              digits={digits}
              onChange={handleDigitsChange}
              suggestions={getSuggestions(digits, availableCells)}
              onSelectSuggestion={handleSelectSuggestion}
              disabled={cellsLoading || createTaskMutation.isPending}
              hasError={!!cellError}
            />
            {cellWarn !== null && (
              <p className="text-xs mt-1" style={{ color: '#ffaa00' }}>{cellWarn}</p>
            )}
            {(cellError !== null || converterError !== null) && (
              <p className="text-xs mt-1" style={{ color: '#ff3366' }}>
                {cellError ?? converterError}
                {converterError !== null && (
                  <> —{' '}
                    <button onClick={handleRetry} className="underline" style={{ color: '#ff3366' }}>
                      Повторить
                    </button>
                  </>
                )}
              </p>
            )}
          </div>
          <button
            disabled={isSubmitDisabled}
            onClick={handleSubmit}
            className="px-4 py-2 text-sm font-medium rounded-md bg-accent text-surface disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex-shrink-0 self-end"
          >
            {submitLabel}
          </button>
        </div>
      </div>
      {createTaskMutation.isError && (
        <p className="text-xs mt-2" style={{ color: '#ff3366' }}>
          Не удалось создать задачу. Попробуйте снова.
        </p>
      )}
    </section>
  )
}
