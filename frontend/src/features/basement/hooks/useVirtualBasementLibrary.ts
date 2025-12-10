import { useQuery } from '@tanstack/react-query';
import { fetchBasementStats } from '../api';
import { createVirtualBasementLibrary } from '../../../entities/basement/types';

interface UseVirtualBasementOptions { enabled?: boolean }

export function useVirtualBasementLibrary(opts?: UseVirtualBasementOptions) {
  return useQuery({
    queryKey: ['basement','virtual','stats'],
    queryFn: async () => {
      const stats = await fetchBasementStats();
      return createVirtualBasementLibrary(stats);
    },
    // Disabled by default to avoid triggering problematic endpoint until backend fix
    enabled: opts?.enabled ?? false,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: false,
    initialData: createVirtualBasementLibrary(),
  });
}
