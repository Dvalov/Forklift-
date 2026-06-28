import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restoreTask } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'
import type { Task } from '@/types/api'

export function useRestoreTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: number) => restoreTask(taskId),
    onSuccess: (_, taskId) => {
      queryClient.setQueryData<Task[]>(['tasks', FORKLIFT_ID], old =>
        old?.map(t => t.id === taskId ? { ...t, status: 'pending' } : t)
      )
      queryClient.invalidateQueries({ queryKey: ['tasks', FORKLIFT_ID] })
    },
  })
}
