
'use client';

import React, { useCallback, useMemo } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { Breadcrumb, Button, Spinner } from '@/shared/ui';
import type { BreadcrumbItem } from '@/shared/ui/Breadcrumb';
import { BookshelfDashboardBoard } from '@/features/bookshelf';
import { useLibrary } from '@/features/library';
import type {
  BookshelfDashboardFilter,
  BookshelfDashboardSort,
  BookshelfDashboardItemDto,
} from '@/entities/bookshelf';
import styles from './page.module.css';

const SORT_OPTIONS: BookshelfDashboardSort[] = [
  'recent_activity',
  'name_asc',
  'created_desc',
  'book_count_desc',
];

const FILTER_OPTIONS: BookshelfDashboardFilter[] = [
  'active',
  'all',
  'archived',
];

const DEFAULT_SORT: BookshelfDashboardSort = 'recent_activity';
const DEFAULT_FILTER: BookshelfDashboardFilter = 'active';

const palette = [
  '#4F46E5',
  '#2563EB',
  '#0D9488',
  '#16A34A',
  '#D97706',
  '#DC2626',
  '#9333EA',
  '#0891B2',
];

const deriveDeterministicColor = (seedSource?: string | null) => {
  if (!seedSource) return undefined;
  const seed = seedSource.toLowerCase();
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return palette[hash % palette.length];
};

const parseSort = (value: string | null): BookshelfDashboardSort =>
  SORT_OPTIONS.includes(value as BookshelfDashboardSort) ? (value as BookshelfDashboardSort) : DEFAULT_SORT;

const parseFilter = (value: string | null): BookshelfDashboardFilter =>
  FILTER_OPTIONS.includes(value as BookshelfDashboardFilter)
    ? (value as BookshelfDashboardFilter)
    : DEFAULT_FILTER;

export default function BookshelvesPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const libraryId = searchParams.get('library_id') || undefined;

  const sortParam = searchParams.get('sort');
  const statusParam = searchParams.get('status');

  const sort = useMemo(() => parseSort(sortParam), [sortParam]);
  const statusFilter = useMemo(() => parseFilter(statusParam), [statusParam]);

  const { data: library, isLoading: isLibraryLoading, error: libraryError } = useLibrary(libraryId);

  const fallbackThemeColor = useMemo(() => {
    if (library?.name) return deriveDeterministicColor(`${library.name}-${library.id}`);
    if (libraryId) return deriveDeterministicColor(libraryId);
    return undefined;
  }, [library?.name, library?.id, libraryId]);

  const breadcrumbItems = useMemo<BreadcrumbItem[]>(() => {
    const base: BreadcrumbItem[] = [{ label: '书库列表', href: '/admin/libraries' }];
    if (library && libraryId) {
      base.push({ label: library.name, href: `/admin/libraries/${libraryId}` });
    }
    base.push({ label: '书架运营面板', active: true });
    return base;
  }, [library, libraryId]);

  const updateQueryParam = useCallback(
    (key: string, value: string | undefined, defaultValue?: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (libraryId) {
        params.set('library_id', libraryId);
      } else {
        params.delete('library_id');
      }

      if (!value || (defaultValue && value === defaultValue)) {
        params.delete(key);
      } else {
        params.set(key, value);
      }

      const queryString = params.toString();
      router.replace(queryString ? `${pathname}?${queryString}` : pathname, { scroll: false });
    },
    [libraryId, pathname, router, searchParams],
  );

  const handleSortChange = useCallback(
    (value: BookshelfDashboardSort) => updateQueryParam('sort', value, DEFAULT_SORT),
    [updateQueryParam],
  );

  const handleStatusFilterChange = useCallback(
    (value: BookshelfDashboardFilter) => updateQueryParam('status', value, DEFAULT_FILTER),
    [updateQueryParam],
  );

  const handleOpenLibraries = useCallback(() => {
    router.push('/admin/libraries');
  }, [router]);

  const handleOpenBookshelf = useCallback(
    (item: BookshelfDashboardItemDto) => {
      router.push(`/admin/bookshelves/${item.id}`);
    },
    [router],
  );

  const handleCreateBookshelf = useCallback(() => {
    const basePath = '/admin/bookshelves/new';
    if (libraryId) {
      router.push(`${basePath}?library_id=${libraryId}`);
      return;
    }
    router.push(basePath);
  }, [router, libraryId]);

  return (
    <main className={styles.page}>
      <Breadcrumb items={breadcrumbItems} />

      <div className={styles.container}>
        <header className={styles.pageHeader}>
          <div className={styles.titleGroup}>
            <h1 className={styles.pageTitle}>书架运营面板</h1>
            {libraryId ? (
              isLibraryLoading ? (
                <div className={styles.loadingRow}>
                  <Spinner size="sm" />
                  <span className={styles.subtitle}>正在加载 Library 信息…</span>
                </div>
              ) : library ? (
                <p className={styles.subtitle}>
                  {library.name}
                  {library.description ? ` · ${library.description}` : ''}
                </p>
              ) : libraryError ? (
                <p className={styles.subtitle}>未能读取该 Library：{(libraryError as Error)?.message || '未知错误'}</p>
              ) : (
                <p className={styles.subtitle}>未找到匹配的 Library。</p>
              )
            ) : (
              <p className={styles.subtitle}>请选择一个 Library 查看其书架的结构指标与 Chronicle 活跃度。</p>
            )}
          </div>
          <div className={styles.pageActions}>
            {libraryId && (
              <Button size="sm" variant="secondary" onClick={() => router.push(`/admin/libraries/${libraryId}`)}>
                查看 Library
              </Button>
            )}
            <Button size="sm" variant="secondary" onClick={handleOpenLibraries}>
              返回书库列表
            </Button>
          </div>
        </header>

        {!libraryId && (
          <div className={styles.notice}>
            <p>当前视图依赖 Library 维度的聚合。请选择左侧导航中的某个 Library，或点击下方按钮跳转到书库列表。</p>
            <div className={styles.noticeActions}>
              <Button size="sm" variant="primary" onClick={handleOpenLibraries}>
                选择 Library
              </Button>
            </div>
          </div>
        )}

        {libraryId && libraryError && !library && !isLibraryLoading && (
          <div className={styles.error}>
            <h2>加载 Library 失败</h2>
            <p>{(libraryError as Error)?.message || '未知错误'}</p>
          </div>
        )}

        {libraryId && (!libraryError || library) && (
          <section className={styles.dashboardSection}>
            <BookshelfDashboardBoard
              libraryId={libraryId}
              sort={sort}
              statusFilter={statusFilter}
              fallbackThemeColor={fallbackThemeColor}
              libraryTags={library?.tags}
              onSortChange={handleSortChange}
              onStatusFilterChange={handleStatusFilterChange}
              onOpenBookshelf={handleOpenBookshelf}
              onCreateBookshelf={handleCreateBookshelf}
            />
          </section>
        )}
      </div>
    </main>
  );
}
