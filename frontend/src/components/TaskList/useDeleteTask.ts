import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteTask } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'

export function useDeleteTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: number) => deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', FORKLIFT_ID] })
    },
  })
}
