import { useInfiniteQuery } from '@tanstack/react-query';
import { listBooks, BookListPage } from './api';

interface UsePaginatedBooksOptions {
  bookshelfId?: string;
  pageSize?: number;
}

// Infinite scroll hook (horizontal or grid) using backend skip/limit
export function usePaginatedBooks({ bookshelfId, pageSize = 20 }: UsePaginatedBooksOptions) {
  const query = useInfiniteQuery<BookListPage>({
    queryKey: ['books', 'paginated', { bookshelfId, pageSize }],
    initialPageParam: 1,
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.page + 1 : undefined),
    queryFn: async ({ pageParam }) => {
      const page = typeof pageParam === 'number' ? pageParam : 1;
      return listBooks(bookshelfId, page, pageSize);
    },
    staleTime: 1000 * 60 * 5,
    placeholderData: (previous) => previous,
  });

  // 计算是否还有更多（基于最后一页长度）
  const pages = query.data?.pages || [];
  const lastPage = pages[pages.length - 1];
  const hasMore = lastPage?.has_more ?? false;

  const books = pages.flatMap((page) => page.items);

  return { ...query, hasMore, books };
}

