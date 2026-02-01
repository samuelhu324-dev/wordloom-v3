import React, { useEffect, useMemo, useState } from 'react';
import type { AxiosError } from 'axios';
import { BookshelfDto, CreateBookshelfRequest } from '@/entities/bookshelf';
import { BookshelfList, useCreateBookshelf } from '@/features/bookshelf';
import { LibraryForm, LibraryFormSubmitPayload, LibraryFormTagValue } from '@/features/library';
import { DEFAULT_TAG_COLOR } from '@/features/library/constants';
import { createTag as createGlobalTag, searchTags as searchGlobalTags } from '@/features/tag/model/api';
import { Button } from '@/shared/ui';
import { showToast } from '@/shared/ui/toast';
import styles from './BookshelfMainWidget.module.css';

interface BookshelfMainWidgetProps {
  libraryId: string;
  bookshelves: BookshelfDto[];
  totalBookshelves?: number;
  isLoading?: boolean;
  error?: any;
  onSelectBookshelf?: (id: string) => void;
  onViewAll?: () => void;
}

// 仅 List 模式，移除 Grid/偏好持久化
type SortOption = 'updated_desc' | 'name_asc' | 'book_count_desc';
type StatusFilter = 'all' | 'active' | 'archived';

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'updated_desc', label: '最近更新' },
  { value: 'name_asc', label: '名称 A-Z' },
  { value: 'book_count_desc', label: '书本数量' },
];

const FILTER_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: '仅 Active' },
  { value: 'archived', label: '仅 Archived' },
];

const TAG_LIMIT = 3;

export const BookshelfMainWidget = React.forwardRef<HTMLDivElement, BookshelfMainWidgetProps>(
  ({ libraryId, bookshelves, totalBookshelves, isLoading, error, onSelectBookshelf, onViewAll }, ref) => {
    const MAX_BOOKSHELVES = 100;
    const WARN_THRESHOLD = 80;
    const bookshelfTotalCount = typeof totalBookshelves === 'number' ? totalBookshelves : bookshelves.length;
    const isAtLimit = bookshelfTotalCount >= MAX_BOOKSHELVES;
    const showProgress = bookshelfTotalCount >= WARN_THRESHOLD;
    const progressPercentage = Math.min(100, (bookshelfTotalCount / MAX_BOOKSHELVES) * 100);
    const limitMessage = isAtLimit
      ? '已达到 100 个书橱上限，请整理或归档后再创建新的书橱。'
      : '接近书橱数量上限，建议整理或归档部分书橱。';
    const countLabel = `${bookshelfTotalCount}/${MAX_BOOKSHELVES} 书橱`;

    // Create dialog state
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Create bookshelf mutation with async interface
    const { mutateAsync: createBookshelfAsync, isPending: isCreating } = useCreateBookshelf();
    const isFormLoading = isSaving || isCreating;

    useEffect(() => {
      if (isAtLimit && isFormOpen) {
        setIsFormOpen(false);
      }
    }, [isAtLimit, isFormOpen]);

    // 仅 List 视图，不做本地持久化
    const [sortOption, setSortOption] = useState<SortOption>('updated_desc');
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [sortRefreshTick, setSortRefreshTick] = useState(0);

    const handleSortChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
      setSortOption(event.target.value as SortOption);
      setSortRefreshTick((t) => t + 1);
    };

    const handleSortRefresh = () => setSortRefreshTick((t) => t + 1);
    const handleFilterChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
      setStatusFilter(event.target.value as StatusFilter);
    };

    const derivedBookshelves = useMemo(() => {
      let list = [...bookshelves];
      if (statusFilter === 'active') {
        list = list.filter(item => (item.status || 'active') === 'active');
      } else if (statusFilter === 'archived') {
        list = list.filter(item => (item.status || '').toLowerCase() === 'archived');
      }

      switch (sortOption) {
        case 'name_asc':
          list.sort((a, b) => a.name.localeCompare(b.name, 'zh-Hans-CN'));
          break;
        case 'book_count_desc':
          list.sort((a, b) => (b.book_count || 0) - (a.book_count || 0));
          break;
        case 'updated_desc':
        default:
          list.sort((a, b) => {
            const aTime = a.updated_at ? new Date(a.updated_at).getTime() : 0;
            const bTime = b.updated_at ? new Date(b.updated_at).getTime() : 0;
            return bTime - aTime;
          });
          break;
      }

      return list;
    }, [bookshelves, sortOption, statusFilter, sortRefreshTick]);

    const hasBookshelves = derivedBookshelves.length > 0;
    const shouldShowList = isLoading || hasBookshelves;

    const handleOpenForm = () => {
      if (isAtLimit) {
        showToast('已达到 100 个书橱上限，请整理或归档后再创建新的书橱。');
        return;
      }
      setIsFormOpen(true);
    };

    const handleCloseForm = () => {
      if (isFormLoading) return;
      setIsFormOpen(false);
    };

    const handleCreateBookshelf = async ({ formValues, tags }: LibraryFormSubmitPayload) => {
      if (isAtLimit) {
        showToast('已达到 100 个书橱上限，请整理或归档后再创建新的书橱。');
        return;
      }

      setIsSaving(true);
      try {
        const normalizedTags = normalizeTagSelections(tags);
        const tagIds = await ensureTagIds(normalizedTags);
        const payload: CreateBookshelfRequest = {
          name: formValues.name,
          description: formValues.description,
          library_id: libraryId,
        };
        if (tagIds.length > 0) {
          payload.tag_ids = tagIds;
        }

        await createBookshelfAsync(payload);
        showToast('书橱已创建');
        setIsFormOpen(false);
      } catch (err) {
        console.error('创建书橱失败:', err);
        const message = extractApiErrorMessage(err);
        showToast(`创建失败：${message}`);
      } finally {
        setIsSaving(false);
      }
    };

    if (error) {
      const status = (error as any)?.response?.status;
      const detail: string | undefined = (error as any)?.response?.data?.detail;
      return (
        <div ref={ref} className={styles.widget}>
          <div className={styles.header}>
            <div className={styles.titleSection}>
              <h2>书橱</h2>
              <div className={styles.countSummary}>
                <span className={styles.countBadge}>{countLabel}</span>
                {showProgress && (
                  <div className={styles.limitNotice}>
                    <div className={styles.progressTrack} aria-hidden="true">
                      <div
                        className={styles.progressValue}
                        style={{ width: `${progressPercentage}%` }}
                      />
                    </div>
                    <span className={styles.limitMessage}>{limitMessage}</span>
                  </div>
                )}
              </div>
            </div>
            <div className={styles.controls}>
              {onViewAll && (
                <Button variant="secondary" size="sm" onClick={onViewAll}>查看全部</Button>
              )}
              <div className={styles.selectControl}>
                <label htmlFor={`bookshelf-sort-${libraryId}`}>排序</label>
                <select id={`bookshelf-sort-${libraryId}`} value={sortOption} onChange={handleSortChange}>
                  {SORT_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div className={styles.selectControl}>
                <label htmlFor={`bookshelf-filter-${libraryId}`}>筛选</label>
                <select id={`bookshelf-filter-${libraryId}`} value={statusFilter} onChange={handleFilterChange}>
                  {FILTER_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <Button
                variant="primary"
                onClick={handleOpenForm}
                disabled={isCreating || isAtLimit}
                title={isAtLimit ? '书橱已达 100 个上限，整理后可继续创建' : undefined}
              >
                {isAtLimit ? '达到上限' : isCreating ? '创建中...' : '新建书橱'}
              </Button>
            </div>
          </div>
          <div style={{background:'var(--color-danger-bg)',padding:'var(--spacing-md)',borderRadius:'var(--radius-md)',color:'var(--color-danger-text)',marginBottom:'var(--spacing-md)'}}>
            书橱加载失败 {status ? `HTTP ${status}` : ''}
            {detail && <div style={{marginTop:'4px',fontSize:'12px',opacity:.8}}>{detail}</div>}
          </div>
          <BookshelfList
            bookshelves={[]}
            isLoading={false}
            onSelectBookshelf={onSelectBookshelf}
          />
        </div>
      );
    }

    return (
      <div ref={ref} className={styles.widget}>
        <div className={styles.header}>
          <div className={styles.titleSection}>
            <h2>书橱</h2>
            <div className={styles.countSummary}>
              <span className={styles.countBadge}>{countLabel}</span>
              {showProgress && (
                <div className={styles.limitNotice}>
                  <div className={styles.progressTrack} aria-hidden="true">
                    <div
                      className={styles.progressValue}
                      style={{ width: `${progressPercentage}%` }}
                    />
                  </div>
                  <span className={styles.limitMessage}>{limitMessage}</span>
                </div>
              )}
            </div>
          </div>
          <div className={styles.controls}>
            {onViewAll && (
              <Button variant="secondary" size="sm" onClick={onViewAll}>查看全部</Button>
            )}
            <div className={styles.selectControl}>
              <label htmlFor={`bookshelf-sort-${libraryId}`}>排序</label>
              <div className={styles.selectRow}>
                <select id={`bookshelf-sort-${libraryId}`} value={sortOption} onChange={handleSortChange}>
                  {SORT_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
                <Button variant="secondary" size="sm" onClick={handleSortRefresh} title="刷新排序">
                  刷新
                </Button>
              </div>
            </div>
            <div className={styles.selectControl}>
              <label htmlFor={`bookshelf-filter-${libraryId}`}>筛选</label>
              <select id={`bookshelf-filter-${libraryId}`} value={statusFilter} onChange={handleFilterChange}>
                {FILTER_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
            <Button
              variant="primary"
              onClick={handleOpenForm}
              disabled={isCreating || isAtLimit}
              type="button"
              title={isAtLimit ? '书橱已达 100 个上限，整理后可继续创建' : undefined}
            >
              {isAtLimit ? '达到上限' : isCreating ? '创建中...' : '新建书橱'}
            </Button>
          </div>
        </div>

        {shouldShowList ? (
          <BookshelfList
            bookshelves={derivedBookshelves}
            isLoading={isLoading}
            onSelectBookshelf={onSelectBookshelf}
          />
        ) : (
          <div className={styles.noResult}>
            <p>No bookshelves yet</p>
          </div>
        )}
        <LibraryForm
          isOpen={isFormOpen}
          mode="create"
          onClose={handleCloseForm}
          onSubmit={handleCreateBookshelf}
          isLoading={isFormLoading}
          isTagPrefillLoading={false}
          maxTags={TAG_LIMIT}
          createTitle="新建书橱"
          createSubtitle="为这个书橱添加简介和标签，稍后仍可修改。"
          nameLabel="书橱名称"
          namePlaceholder="例如：阅读中"
          descriptionLabel="简介（可选）"
          descriptionPlaceholder="例如：我正在阅读的书籍..."
          createSubmitLabel="创建"
          showThemeColorField={false}
        />
      </div>
    );
  }
);

BookshelfMainWidget.displayName = 'BookshelfMainWidget';

function normalizeTagSelections(tags: LibraryFormTagValue[] = []): LibraryFormTagValue[] {
  const normalized: LibraryFormTagValue[] = [];
  const seen = new Set<string>();
  for (const tag of tags ?? []) {
    const trimmed = (tag.name || '').trim();
    if (!trimmed) continue;
    const key = tag.id || trimmed.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    normalized.push({
      ...tag,
      name: trimmed,
    });
    if (normalized.length >= TAG_LIMIT) break;
  }
  return normalized;
}

async function ensureTagIds(tags: LibraryFormTagValue[] = []): Promise<string[]> {
  const ids: string[] = [];
  for (const tag of tags) {
    if (tag.id) {
      ids.push(tag.id);
      continue;
    }
    const resolvedName = (tag.name || '').trim();
    if (!resolvedName) {
      continue;
    }
    ids.push(await resolveTagId(resolvedName));
  }
  return ids;
}

async function resolveTagId(name: string): Promise<string> {
  try {
    const created = await createGlobalTag({ name, color: DEFAULT_TAG_COLOR });
    return created.id;
  } catch (error) {
    if (isConflictError(error)) {
      const matches = await searchGlobalTags({ keyword: name, limit: 5 });
      const exact = matches.find((tag) => tag.name?.trim().toLowerCase() === name.trim().toLowerCase());
      if (exact?.id) {
        return exact.id;
      }
    }
    throw error;
  }
}

function extractApiErrorMessage(error: unknown): string {
  const detail = (error as any)?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        const loc = Array.isArray(item?.loc) ? item.loc.join('.') : item?.loc;
        const msg = item?.msg || item?.message || '';
        return loc ? `${loc}: ${msg}` : msg || JSON.stringify(item ?? {});
      })
      .filter(Boolean)
      .join(' | ');
  }
  if (typeof detail === 'string') return detail;
  if (detail?.message) return detail.message;
  const message = (error as Error)?.message;
  return message || '未知错误';
}

function isConflictError(error: unknown): error is AxiosError<any> {
  const axiosError = error as AxiosError<any> | undefined;
  return Boolean(axiosError?.response && axiosError.response.status === 409);
}
