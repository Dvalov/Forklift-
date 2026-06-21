import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cancelTask } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'

export function useCancelTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: number) => cancelTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', FORKLIFT_ID] })
    },
  })
}
