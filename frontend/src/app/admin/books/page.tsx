'use client';

import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import { Breadcrumb } from '@/shared/ui';
import { useBooks } from '@/features/book';
import { useBookshelf } from '@/features/bookshelf';
import { useLibrary } from '@/features/library';
import { getLibraryTags } from '@/features/library/model/api';
import type { LibraryTagSummaryDto } from '@/entities/library';
import {
  buildTagDescriptionsMap,
  mergeTagDescriptionMaps,
} from '@/features/tag/lib/tagCatalog';
import { BookMaturityView, buildBookMaturitySnapshot } from '@/widgets/book/BookMainWidget';
import { useI18n } from '@/i18n/useI18n';
import styles from './page.module.css';

type LibraryTagCatalogEntry = {
  libraryId: string;
  tags: LibraryTagSummaryDto[];
};

/**
 * Books List Page (Global)
 * Route: /admin/books
 * Query: ?bookshelf_id={bookshelfId} (optional)
 *
 * Displays all books (or filtered by bookshelf_id)
 * - List all books for current user
 * - Support filtering by bookshelf_id via query param
 * - Navigate to book detail
 */
export default function BooksPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookshelfId = searchParams.get('bookshelf_id') || undefined;
  const { t } = useI18n();

  const {
    data: bookList,
    isLoading,
    error,
  } = useBooks(bookshelfId);

  const normalizedBooks = useMemo(() => {
    const items = (bookList as any)?.items;
    return Array.isArray(items) ? items : [];
  }, [bookList]);

  const totalBooks = (bookList as any)?.total;

  const snapshot = useMemo(() => (
    buildBookMaturitySnapshot(normalizedBooks, totalBooks)
  ), [normalizedBooks, totalBooks]);

  const {
    data: bookshelf,
  } = useBookshelf(bookshelfId || '');

  const { data: library } = useLibrary(bookshelf?.library_id || undefined);

  const inlineTagDescriptions = useMemo(
    () => buildTagDescriptionsMap(library?.tags, { libraryId: library?.id ?? null }),
    [library?.tags, library?.id],
  );

  const hasTaggedBooks = useMemo(
    () => normalizedBooks.some((book) => Array.isArray(book.tagsSummary) && book.tagsSummary.length > 0),
    [normalizedBooks],
  );

  const taggedLibraryIds = useMemo(() => {
    if (!hasTaggedBooks) {
      return [] as string[];
    }
    const unique = new Set<string>();
    normalizedBooks.forEach((book) => {
      if (book.library_id && Array.isArray(book.tagsSummary) && book.tagsSummary.length > 0) {
        unique.add(book.library_id);
      }
    });
    return Array.from(unique).sort();
  }, [normalizedBooks, hasTaggedBooks]);

  const targetLibraryId = library?.id || bookshelf?.library_id;

  const shouldFetchTagCatalog = useMemo(() => {
    if (!targetLibraryId || !hasTaggedBooks) {
      return false;
    }
    if (!inlineTagDescriptions) {
      return true;
    }
    return normalizedBooks.some((book) => book.tagsSummary?.some((tag) => {
      const normalized = tag?.trim().toLowerCase();
      return normalized ? !inlineTagDescriptions[normalized] : false;
    }));
  }, [normalizedBooks, hasTaggedBooks, inlineTagDescriptions, targetLibraryId]);

  const { data: fetchedLibraryTags } = useQuery({
    queryKey: ['library-tag-catalog', targetLibraryId],
    queryFn: () => getLibraryTags(targetLibraryId!, 200),
    enabled: shouldFetchTagCatalog,
    staleTime: 5 * 60 * 1000,
  });

  const fetchedTagDescriptions = useMemo(
    () => buildTagDescriptionsMap(fetchedLibraryTags?.tags, { libraryId: targetLibraryId ?? null }),
    [fetchedLibraryTags?.tags, targetLibraryId],
  );

  const shouldFetchGlobalTagCatalog = useMemo(() => (
    !bookshelfId && taggedLibraryIds.length > 0
  ), [bookshelfId, taggedLibraryIds]);

  const { data: multiLibraryTagCatalog } = useQuery<LibraryTagCatalogEntry[]>({
    queryKey: ['library-tag-catalog-multi', taggedLibraryIds],
    queryFn: async () => {
      const responses = await Promise.all(taggedLibraryIds.map(async (libraryId) => {
        try {
          const payload = await getLibraryTags(libraryId, 200);
          return { libraryId, tags: payload?.tags ?? [] };
        } catch (err) {
          console.warn('[books-page] Failed to load tag catalog for library', libraryId, err);
          return { libraryId, tags: [] as LibraryTagSummaryDto[] };
        }
      }));
      return responses;
    },
    enabled: shouldFetchGlobalTagCatalog,
    staleTime: 5 * 60 * 1000,
  });

  const multiLibraryTagDescriptions = useMemo(() => {
    if (!multiLibraryTagCatalog || multiLibraryTagCatalog.length === 0) {
      return undefined;
    }
    const scopedMaps = multiLibraryTagCatalog
      .map(({ libraryId, tags }) => buildTagDescriptionsMap(tags, { libraryId, includeUnscoped: false }))
      .filter((map): map is Record<string, string> => Boolean(map));
    if (!scopedMaps.length) {
      return undefined;
    }
    return mergeTagDescriptionMaps(...scopedMaps);
  }, [multiLibraryTagCatalog]);

  const tagDescriptionsMap = useMemo(
    () => mergeTagDescriptionMaps(inlineTagDescriptions, fetchedTagDescriptions, multiLibraryTagDescriptions),
    [inlineTagDescriptions, fetchedTagDescriptions, multiLibraryTagDescriptions],
  );

  const handleSelectBook = (bookId: string) => {
    router.push(`/admin/books/${bookId}`);
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <p>加载中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.error}>
          <h2>加载书籍列表失败</h2>
          <p>{error?.message || '未知错误'}</p>
        </div>
      </div>
    );
  }

  return (
    <main className={styles.page}>
      <div className={styles.inner}>
        <Breadcrumb
          items={[
            { label: t('bookshelves.library.breadcrumb.list'), href: '/admin/libraries' },
            bookshelfId && bookshelf ? { label: bookshelf.name, href: `/admin/bookshelves/${bookshelf.id}` } : null,
            { label: '书籍概览', active: true },
          ].filter(Boolean) as any}
        />

        <header className={styles.hero}>
          <div>
            <h1>书籍概览</h1>
            <p className={styles.subtitle}>
              {bookshelfId && bookshelf
                ? `正在查看「${bookshelf.name}」中的书籍，支持按成熟度分区快速定位。`
                : '查看所有书籍的成熟度分布，点击卡片可进入对应书籍的块编辑页。'}
            </p>
          </div>
        </header>

        <BookMaturityView
          snapshot={snapshot}
          isLoading={isLoading}
          onSelectBook={handleSelectBook}
          tagDescriptionsMap={tagDescriptionsMap}
        />
      </div>
    </main>
  );
}
