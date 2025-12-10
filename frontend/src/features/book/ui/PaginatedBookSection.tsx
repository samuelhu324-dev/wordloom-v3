"use client";
import React from 'react';
import { useBookshelf } from '@/features/bookshelf';
import { useLibrary, useLibraryTagCatalog } from '@/features/library';
import { usePaginatedBooks } from '../model/usePaginatedBooks';
import { BookPreviewList } from './BookPreviewList';
import { BookLayoutToggle } from './BookLayoutToggle';

interface PaginatedBookSectionProps {
  bookshelfId?: string;
  pageSize?: number;
}

export const PaginatedBookSection: React.FC<PaginatedBookSectionProps> = ({ bookshelfId, pageSize = 20 }) => {
  const [layout, setLayout] = React.useState<'horizontal' | 'grid'>('horizontal');
  const { books, isLoading, fetchNextPage, hasMore, isFetchingNextPage } = usePaginatedBooks({ bookshelfId, pageSize });
  const { data: bookshelf } = useBookshelf(bookshelfId || '');

  // Books fetched without a bookshelf filter can still belong to a single library; reuse that id when possible.
  const inferredLibraryId = React.useMemo(() => {
    const ids = new Set<string>();
    books.forEach((book) => {
      if (book.library_id) {
        ids.add(book.library_id);
      }
    });
    return ids.size === 1 ? Array.from(ids)[0] : undefined;
  }, [books]);

  const resolvedLibraryId = bookshelf?.library_id || inferredLibraryId;
  const { data: library } = useLibrary(resolvedLibraryId);

  const taggableBooks = React.useMemo(() => (
    books.filter((book) => Array.isArray(book.tagsSummary) && book.tagsSummary.length > 0)
  ), [books]);

  const requiredTagLabels = React.useMemo(() => {
    if (!taggableBooks.length) {
      return [] as string[];
    }
    const unique = new Set<string>();
    taggableBooks.forEach((book) => {
      book.tagsSummary?.forEach((tag) => {
        const normalized = tag?.trim();
        if (normalized) {
          unique.add(normalized);
        }
      });
    });
    return Array.from(unique);
  }, [taggableBooks]);

  const { tagDescriptionsMap } = useLibraryTagCatalog({
    libraryId: resolvedLibraryId,
    inlineTags: library?.tags,
    requiredTagLabels,
    enabled: Boolean(resolvedLibraryId) && requiredTagLabels.length > 0,
  });

  return (
    <section>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h2 style={{ margin: 0, fontSize: '16px' }}>书籍列表</h2>
        <BookLayoutToggle layout={layout} onChange={setLayout} />
      </div>
      <BookPreviewList
        books={books}
        isLoading={isLoading && books.length === 0}
        layout={layout}
        hasMore={hasMore}
        onLoadMore={() => fetchNextPage()}
        useIntersection={layout === 'grid'}
        tagDescriptionsMap={tagDescriptionsMap}
      />
      {isFetchingNextPage && <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>加载更多...</p>}
      {!hasMore && books.length > 0 && <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>已到末尾</p>}
    </section>
  );
};
