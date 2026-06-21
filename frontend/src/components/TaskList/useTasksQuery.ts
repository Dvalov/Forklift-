import { useQuery } from '@tanstack/react-query'
import { getTasks } from '@/api/tasks'
import { FORKLIFT_ID } from '@/config'
import type { Task } from '@/types/api'

export function useTasksQuery(): {
  data: Task[] | undefined
  isLoading: boolean
  isError: boolean
} {
  const query = useQuery({
    queryKey: ['tasks', FORKLIFT_ID],
    queryFn: async () => {
      const { data, error } = await getTasks()
      if (error) throw new Error(error)
      return data as Task[]
    },
    refetchInterval: 5000,
    refetchIntervalInBackground: true,
  })

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
  }
}
