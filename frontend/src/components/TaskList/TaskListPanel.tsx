import React, { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import ActiveTaskList from './ActiveTaskList'
import TaskHistoryList from './TaskHistoryList'
import { syncFromOneC, getAllCells } from '@/api/warehouse'
import { updateForkliftCellPosition } from '@/api/forklift'
import { WAREHOUSE_ID, FORKLIFT_ID } from '@/config'
import { checkForkliftBoundary } from '@/lib/boundaryCheck'
import type { Cell, Forklift } from '@/types/api'

class TaskListErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <p className="text-sm p-4" style={{ color: '#ff3366' }}>
          Панель задач недоступна
        </p>
      )
    }
    return this.props.children
  }
}

export default function TaskListPanel() {
  const queryClient = useQueryClient()
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const syncMutation = useMutation({
    mutationFn: async () => {
      const result = await syncFromOneC()
      if (!result.data) throw new Error(result.error ?? 'sync failed')
      return result.data
    },
    onSuccess: async (data) => {
      setSuccessMsg(`Синхронизировано: ${data.synced} ячеек, удалено: ${data.deleted}`)

      const freshCells = await queryClient.fetchQuery<Cell[]>({
        queryKey: ['allCells', WAREHOUSE_ID],
        queryFn: async () => {
          const result = await getAllCells()
          return result.data ?? []
        },
        staleTime: 0,
      })

      const forklift = queryClient.getQueryData<Forklift>(['forklift', FORKLIFT_ID])
      if (!forklift || freshCells.length === 0) return

      const correction = checkForkliftBoundary(forklift, freshCells)
      if (!correction) return

      const { error } = await updateForkliftCellPosition(FORKLIFT_ID, correction.cellX, correction.cellZ)
      if (!error) {
        void queryClient.invalidateQueries({ queryKey: ['forklift', FORKLIFT_ID] })
        setSuccessMsg(prev => `${prev ?? ''} · Погрузчик скорректирован`)
      }
    },
    onError: () => {
      setErrorMsg('Ошибка синхронизации')
    },
  })

  useEffect(() => {
    if (!successMsg) return
    const timer = setTimeout(() => {
      setSuccessMsg(null)
    }, 5000)
    return () => clearTimeout(timer)
  }, [successMsg])

  function handleSync() {
    setSuccessMsg(null)
    setErrorMsg(null)
    syncMutation.mutate()
  }

  return (
    <TaskListErrorBoundary>
      <div className="flex flex-col gap-4">
        <div
          style={{
            background: 'rgba(0,0,0,0.4)',
            backdropFilter: 'blur(5px)',
            WebkitBackdropFilter: 'blur(5px)',
            border: '1px solid rgba(0,255,255,0.1)',
            borderRadius: 16,
            padding: 16,
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <h2
              style={{
                borderLeft: '3px solid #00ffff',
                paddingLeft: '12px',
                color: '#8ab4f8',
                fontSize: '16px',
                fontWeight: 600,
              }}
            >
              Задачи
            </h2>
            <button
              onClick={handleSync}
              disabled={syncMutation.isPending}
              style={{
                background: 'rgba(0,255,255,0.08)',
                border: '1px solid rgba(0,255,255,0.3)',
                color: '#00ffff',
                borderRadius: 8,
                padding: '5px 12px',
                fontSize: 13,
                cursor: syncMutation.isPending ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                opacity: syncMutation.isPending ? 0.5 : 1,
              }}
            >
              {syncMutation.isPending && (
                <svg
                  className="animate-spin"
                  width={14}
                  height={14}
                  viewBox="0 0 14 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <circle
                    cx="7"
                    cy="7"
                    r="5"
                    stroke="rgba(0,255,255,0.3)"
                    strokeWidth="2"
                  />
                  <path
                    d="M7 2a5 5 0 0 1 5 5"
                    stroke="#00ffff"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              )}
              Синхр. ячейки из 1С
            </button>
          </div>
          {successMsg && (
            <p style={{ color: '#00ffff', fontSize: 13, margin: 0 }}>{successMsg}</p>
          )}
          {errorMsg && (
            <p style={{ color: '#ff3366', fontSize: 13, margin: 0 }}>{errorMsg}</p>
          )}
        </div>
        <ActiveTaskList />
        <TaskHistoryList />
      </div>
    </TaskListErrorBoundary>
  )
}
