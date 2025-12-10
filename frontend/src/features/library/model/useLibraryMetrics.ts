"use client";
import { useEffect, useRef, useState } from 'react';
import { listBookshelves } from '@/features/bookshelf/model/api';
import { listBooks } from '@/features/book/model/api';
import type { LibraryDto } from '@/entities/library';

// In-memory cache across component mounts (session scope)
const metricsCache: Record<string, { bookshelves: number | null; books: number | null }> = {};

interface UseLibraryMetricsResult {
  metrics: Record<string, { bookshelves: number | null; books: number | null }>;
  loadingIds: Set<string>;
}

export function useLibraryMetrics(libraries: LibraryDto[] | undefined) : UseLibraryMetricsResult {
  const [metrics, setMetrics] = useState<Record<string, { bookshelves: number | null; books: number | null }>>({});
  const loadingIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!libraries || libraries.length === 0) return;
    let cancelled = false;

    const fetchMetrics = async (libraryId: string) => {
      // Already cached
      if (metricsCache[libraryId]) {
        setMetrics(prev => ({ ...prev, [libraryId]: metricsCache[libraryId] }));
        return;
      }
      loadingIdsRef.current.add(libraryId);
      try {
        const shelvesPage = await listBookshelves({ libraryId, page: 1, pageSize: 100 });
        const shelves = shelvesPage.items;
        // Parallel fetch minimal book counts (only first page meta per shelf)
        const bookTotals = await Promise.allSettled(
          shelves.map(shelf => listBooks(shelf.id, 1, 1))
        );
        let totalBooks = 0;
        for (const r of bookTotals) {
          if (r.status === 'fulfilled') {
            totalBooks += r.value.total;
          }
        }
        const entry = { bookshelves: shelvesPage.total, books: totalBooks };
        metricsCache[libraryId] = entry;
        if (!cancelled) {
          setMetrics(prev => ({ ...prev, [libraryId]: entry }));
        }
      } catch {
        const entry = { bookshelves: null, books: null };
        metricsCache[libraryId] = entry; // cache failure to avoid loops
        if (!cancelled) {
          setMetrics(prev => ({ ...prev, [libraryId]: entry }));
        }
      } finally {
        loadingIdsRef.current.delete(libraryId);
      }
    };

    // Fire off sequential (could batch concurrency later)
    (async () => {
      for (const lib of libraries) {
        if (cancelled) break;
        await fetchMetrics(lib.id);
      }
    })();

    return () => { cancelled = true; };
  }, [libraries]);

  return { metrics, loadingIds: loadingIdsRef.current };
}
