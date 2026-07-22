import { useQuery } from '@tanstack/react-query'
import { getAllCells } from '@/api/warehouse'
import { WAREHOUSE_ID } from '@/config'
import type { Cell } from '@/types/api'

export function useAllCellsQuery(): Cell[] {
  const { data } = useQuery({
    queryKey: ['allCells', WAREHOUSE_ID],
    queryFn: async () => {
      const { data, error } = await getAllCells()
      if (error || !data) return [] as Cell[]
      return data
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
    refetchIntervalInBackground: true,
  })
  return data ?? []
}
