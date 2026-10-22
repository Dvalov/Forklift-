import { useQuery } from '@tanstack/react-query'
import { getAvailableCells } from '@/api/warehouse'
import { WAREHOUSE_ID } from '@/config'
import type { Cell } from '@/types/api'

export function useAvailableCells(): Cell[] {
  const { data } = useQuery({
    queryKey: ['cells', WAREHOUSE_ID],
    queryFn: async () => {
      const { data, error } = await getAvailableCells()
      if (error || !data) return [] as Cell[]
      return data
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
    refetchIntervalInBackground: true,
  })
  return data ?? []
}
