import { useQuery } from '@tanstack/react-query'
import { getAnyLogicState } from '@/api/anylogic'
import type { AnyLogicState } from '@/types/api'

export function useAnyLogicQuery(): AnyLogicState | null {
  const { data } = useQuery<AnyLogicState | null>({
    queryKey: ['anylogic', 'state'],
    queryFn: async () => {
      const { data, error } = await getAnyLogicState()
      if (error || !data) return null
      return data
    },
    staleTime: 3000,
    refetchInterval: 3000,
    refetchIntervalInBackground: true,
    retry: false,
  })
  return data ?? null
}
