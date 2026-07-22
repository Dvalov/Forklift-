import { useQuery } from '@tanstack/react-query'
import { getForklift } from '@/api/forklift'
import { FORKLIFT_ID } from '@/config'
import type { Forklift } from '@/types/api'

export function useForkliftQuery(): {
  data: Forklift | undefined
  isLoading: boolean
  isError: boolean
  lastSuccessAt: number | null
} {
  const query = useQuery({
    queryKey: ['forklift', FORKLIFT_ID],
    queryFn: async () => {
      const { data, error } = await getForklift()
      if (error) throw new Error(error)
      return data as Forklift
    },
    refetchInterval: 3000,
    refetchIntervalInBackground: true,
  })

  const lastSuccessAt: number | null = query.dataUpdatedAt > 0 ? query.dataUpdatedAt : null

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    lastSuccessAt,
  }
}
