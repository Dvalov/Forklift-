import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cancelTask } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'
import type { Task } from '@/types/api'

export function useCancelTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: number) => cancelTask(taskId),
    onSuccess: (_, taskId) => {
      queryClient.setQueryData<Task[]>(['tasks', FORKLIFT_ID], old =>
        old?.map(t => t.id === taskId ? { ...t, status: 'cancelled' } : t)
      )
      queryClient.invalidateQueries({ queryKey: ['tasks', FORKLIFT_ID] })
    },
  })
}
