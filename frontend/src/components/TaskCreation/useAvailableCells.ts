import { useQuery } from '@tanstack/react-query'
import { getAvailableCells } from '@/api/warehouse'
import { WAREHOUSE_ID } from '@/config'

export function useAvailableCells() {
  return useQuery({
    queryKey: ['cells', WAREHOUSE_ID],
    queryFn: () => getAvailableCells(),
    staleTime: 30_000,
  })
}
