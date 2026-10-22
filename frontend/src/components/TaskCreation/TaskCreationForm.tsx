import { useState, useEffect, useMemo } from 'react'
import { useAvailableCells } from './useAvailableCells'
import { useCreateTask } from './useCreateTask'
import { useTasksQuery } from '@/components/TaskList/useTasksQuery'
import { convertCellToCoords } from '@/api/converter'
import { FORKLIFT_ID } from '@/config'
import type { Cell, Coordinates } from '@/types/api'
import CellNameInput from './CellNameInput'
import { postAnyLogicOrder } from '@/api/anylogic'
import { useAnyLogicQuery } from '@/components/Instruments/useAnyLogicQuery'
import { useAllCellsQuery } from '@/components/Instruments/useAllCellsQuery'
import Toast from '@/components/ui/Toast'

export default function TaskCreationForm() {
  const availableCellsRaw: Cell[] = useAvailableCells()
  const { data: tasks } = useTasksQuery()
  const createTaskMutation = useCreateTask()
  const anylogicState = useAnyLogicQuery()
  const allCells: Cell[] = useAllCellsQuery()
  const [toastVisible, setToastVisible] = useState(false)

  const activeCellKeys = useMemo(() => {
    const active = (tasks ?? []).filter(t => t.status === 'pending' || t.status === 'in_progress')
    return new Set(active.map(t => `${t.dest_cell_x},${t.dest_cell_y},${t.dest_cell_z}`))
  }, [tasks])

  const availableCells = useMemo(
    () => availableCellsRaw.filter(c => !activeCellKeys.has(`${c.x},${c.y},${c.z}`)),
    [availableCellsRaw, activeCellKeys],
  )

  // Source cell state
  const [sourceQuery, setSourceQuery] = useState('')
  const [sourceCell, setSourceCell] = useState<Cell | null>(null)
  const [sourceCellError, setSourceCellError] = useState<string | null>(null)

  // Dest cell state
  const [destQuery, setDestQuery] = useState('')
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

  function handleSourceQueryChange(query: string) {
    setSourceQuery(query)
    setSourceCell(null)
    setSourceCellError(null)
  }

  function handleSourceSelectCell(cell: Cell) {
    setSourceQuery(cell.name || `${cell.x}·${cell.y}·${cell.z}`)
    setSourceCell(cell)
    setSourceCellError(null)
  }

  function handleDestQueryChange(query: string) {
    setDestQuery(query)
    setSelectedCell(null)
    setCoords(null)
    setCellError(null)
    setCellWarn(null)
    setConverterError(null)
  }

  function handleDestSelectCell(cell: Cell) {
    const cellKey = `${cell.x},${cell.y},${cell.z}`
    if (activeCellKeys.has(cellKey)) {
      const activeTask = (tasks ?? []).find(
        t =>
          (t.status === 'pending' || t.status === 'in_progress') &&
          t.dest_cell_x === cell.x && t.dest_cell_y === cell.y && t.dest_cell_z === cell.z,
      )
      const statusLabel = activeTask?.status === 'in_progress' ? 'в работе' : 'ожидает'
      setCellWarn(`Ячейка уже занята задачей: ${statusLabel}`)
      return
    }

    if (!cell.available) {
      setCellError('Ячейка недоступна')
      return
    }

    setDestQuery(cell.name || `${cell.x}·${cell.y}·${cell.z}`)
    setSelectedCell(cell)
    runConverter(cell)
  }

  useEffect(() => {
    if (createTaskMutation.isSuccess) {
      if (sourceCell !== null && selectedCell !== null && anylogicState != null && (anylogicState.cells?.length ?? 0) > 0) {
        const alSource = anylogicState.cells.find(c =>
          (sourceCell.name && c.name === sourceCell.name) || (c.col === sourceCell.x && c.row === sourceCell.z)
        )
        const alDest = anylogicState.cells.find(c =>
          (selectedCell.name && c.name === selectedCell.name) || (c.col === selectedCell.x && c.row === selectedCell.z)
        )
        if (alSource !== undefined && alDest !== undefined) {
          void postAnyLogicOrder(alSource.id, alDest.id)
        } else {
          console.warn('[AnyLogic] cell lookup failed', { source: sourceCell, dest: selectedCell })
        }
      }
      setToastVisible(true)
      setSourceQuery('')
      setSourceCell(null)
      setSourceCellError(null)
      setDestQuery('')
      setSelectedCell(null)
      setCoords(null)
      setCellError(null)
      setCellWarn(null)
      setConverterError(null)
      createTaskMutation.reset()
    }
  }, [createTaskMutation.isSuccess, createTaskMutation, sourceCell, selectedCell, anylogicState])

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
      dest_cell_name: selectedCell.name,
      source_cell_x: sourceCell.x,
      source_cell_y: sourceCell.y,
      source_cell_z: sourceCell.z,
      source_cell_name: sourceCell.name,
    })
  }

  const isSubmitDisabled =
    !sourceCell || !selectedCell || !coords || converterLoading || createTaskMutation.isPending

  const submitLabel =
    converterLoading || createTaskMutation.isPending ? '…' : 'Создать задачу'

  return (
    <>
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
          <CellNameInput
            value={sourceQuery}
            onChange={handleSourceQueryChange}
            cells={allCells}
            onSelectCell={handleSourceSelectCell}
            disabled={createTaskMutation.isPending}
            hasError={!!sourceCellError}
            placeholder="Название ячейки..."
          />
          {sourceCellError && <div style={{ color: '#ff3366', fontSize: 12, marginTop: 4 }}>{sourceCellError}</div>}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <label style={{ color: '#aaa', fontSize: 13, marginBottom: 4, display: 'block' }}>Куда</label>
            <CellNameInput
              value={destQuery}
              onChange={handleDestQueryChange}
              cells={availableCells}
              onSelectCell={handleDestSelectCell}
              disabled={createTaskMutation.isPending}
              hasError={!!cellError}
              placeholder="Название ячейки..."
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
    <Toast message="Задача создана" visible={toastVisible} onHide={() => setToastVisible(false)} />
    </>
  )
}
