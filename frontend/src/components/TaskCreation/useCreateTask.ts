import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createTask } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'
import type { CreateTaskPayload } from '@/types/api'

export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateTaskPayload) => createTask(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', FORKLIFT_ID] })
    },
  })
}
