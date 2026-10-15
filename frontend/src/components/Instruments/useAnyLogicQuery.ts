import { useQuery } from '@tanstack/react-query'
import { getAnyLogicState } from '@/api/anylogic'
import type { AnyLogicState } from '@/types/api'

export function useAnyLogicQuery() {
  return useQuery<AnyLogicState | null>({
    queryKey: ['anylogic', 'state'],
    queryFn: async () => {
      const { data, error } = await getAnyLogicState()
      if (error || !data) return null
      return data
    },
    refetchInterval: 3000,
    retry: false,
    refetchIntervalInBackground: true,
  })
}
