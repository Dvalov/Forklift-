import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteTask } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'
import type { Task } from '@/types/api'

export function useDeleteTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const { error } = await deleteTask(taskId)
      if (error) throw new Error(error)
    },
    onSuccess: (_, taskId) => {
      queryClient.setQueryData<Task[]>(['tasks', FORKLIFT_ID], tasks =>
        tasks?.filter(task => task.id !== taskId)
      )
    },
    onSettled: () => {
      return queryClient.invalidateQueries({ queryKey: ['tasks', FORKLIFT_ID] })
    },
  })
}
