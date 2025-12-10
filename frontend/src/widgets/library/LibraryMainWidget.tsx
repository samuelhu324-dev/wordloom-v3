"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { LayoutGrid, List as ListIcon } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import type { AxiosError } from 'axios';
import {
  useCreateLibrary,
  useQuickUpdateLibrary,
  LibraryList,
  LibraryForm,
  getLibraryTags,
  replaceLibraryTags,
} from '@/features/library';
import { DEFAULT_TAG_COLOR } from '@/features/library/constants';
import type {
  LibrarySortOption,
  LibraryFormSubmitPayload,
  LibraryFormTagValue,
  LibraryTagsResponseDto,
} from '@/features/library';
import type { LibraryDto } from '@/entities/library';
import { Button } from '@/shared/ui';
import { showToast } from '@/shared/ui/toast';
import { createTag as createGlobalTag, searchTags as searchGlobalTags } from '@/features/tag/model/api';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import styles from './LibraryMainWidget.module.css';

const SORT_OPTIONS: { value: LibrarySortOption; labelKey: MessageKey }[] = [
  { value: 'last_activity', labelKey: 'libraries.sort.lastActivity' },
  { value: 'views', labelKey: 'libraries.sort.mostViewed' },
  { value: 'created', labelKey: 'libraries.sort.latestCreated' },
  { value: 'name', labelKey: 'libraries.sort.byName' },
];

const TAG_LIMIT = 3;

interface LibraryMainWidgetProps {
  onSelectLibrary?: (libraryId: string) => void;
  searchQuery?: string;
}

export const LibraryMainWidget = React.forwardRef<HTMLDivElement, LibraryMainWidgetProps>(
  ({ onSelectLibrary, searchQuery = '' }, ref) => {
    const { t } = useI18n();
    const createMutation = useCreateLibrary();
    const quickUpdateMutation = useQuickUpdateLibrary();
    const queryClient = useQueryClient();
    const router = useRouter();
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingLibrary, setEditingLibrary] = useState<LibraryDto | null>(null);
    const [editingLibraryTags, setEditingLibraryTags] = useState<LibraryFormTagValue[]>([]);
    const [isTagPrefillLoading, setIsTagPrefillLoading] = useState(false);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [searchInput, setSearchInput] = useState(searchQuery);
    const [sortOption, setSortOption] = useState<LibrarySortOption>('last_activity');
    const [includeArchived, setIncludeArchived] = useState(false);

    // 初始化读取布局偏好
    useEffect(() => {
      try {
        if (typeof window === 'undefined') return;
        const savedView = localStorage.getItem('wl_libraries_view');
        if (savedView === 'list' || savedView === 'grid') setViewMode(savedView);

        const savedSort = localStorage.getItem('wl_libraries_sort') as LibrarySortOption | null;
        if (savedSort && SORT_OPTIONS.some((option) => option.value === savedSort)) {
          setSortOption(savedSort);
        }

        const savedArchived = localStorage.getItem('wl_libraries_include_archived');
        if (savedArchived === 'true') {
          setIncludeArchived(true);
        }
      } catch (e) {
        // ignore
      }
    }, []);

    useEffect(() => {
      if (!editingLibrary || !isFormOpen) {
        setEditingLibraryTags([]);
        setIsTagPrefillLoading(false);
        return;
      }

      let aborted = false;
      const fetchTags = async () => {
        setIsTagPrefillLoading(true);
        try {
          const response = await getLibraryTags(editingLibrary.id, 25);
          if (aborted) return;
          setEditingLibraryTags(mapTagsResponseToFormValues(response, t('libraries.tags.untitled')));
        } catch (error) {
          if (!aborted) {
            console.error('Failed to load library tags:', error);
            setEditingLibraryTags([]);
          }
        } finally {
          if (!aborted) {
            setIsTagPrefillLoading(false);
          }
        }
      };

      fetchTags();
      return () => {
        aborted = true;
      };
    }, [editingLibrary?.id, isFormOpen, t]);

    const toggleView = (mode: 'grid' | 'list') => {
      setViewMode(mode);
      try {
        localStorage.setItem('wl_libraries_view', mode);
      } catch (e) {
        // ignore
      }
    };

    const handleSortChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
      const next = event.target.value as LibrarySortOption;
      setSortOption(next);
      try {
        localStorage.setItem('wl_libraries_sort', next);
      } catch (e) {
        // ignore
      }
    };

    const toggleArchived = () => {
      setIncludeArchived((prev) => {
        const next = !prev;
        try {
          localStorage.setItem('wl_libraries_include_archived', next ? 'true' : 'false');
        } catch (e) {
          // ignore
        }
        return next;
      });
    };

    const extractApiErrorMessage = (error: unknown): string => {
      const responseDetail = (error as any)?.response?.data?.detail;
      if (Array.isArray(responseDetail)) {
        return responseDetail
          .map((item) => {
            if (typeof item === 'string') return item;
            const loc = Array.isArray(item?.loc) ? item.loc.join('.') : item?.loc;
            const msg = item?.msg || item?.message || '';
            return loc ? `${loc}: ${msg}` : msg || JSON.stringify(item ?? {});
          })
          .filter(Boolean)
          .join(' | ');
      }
      if (typeof responseDetail === 'string') {
        return responseDetail;
      }
      if (responseDetail?.message) {
        return responseDetail.message;
      }
      return (error as any)?.message || t('libraries.error.unknown');
    };

    const handleSaveLibrary = async ({ formValues, tags }: LibraryFormSubmitPayload) => {
      try {
        const normalizedTags = normalizeTagSelections(tags);
        const previousTagCount = editingLibrary ? editingLibraryTags.length : 0;
        let targetLibraryId: string;

        if (editingLibrary) {
          await quickUpdateMutation.mutateAsync({ libraryId: editingLibrary.id, data: formValues });
          targetLibraryId = editingLibrary.id;
        } else {
          const created = await createMutation.mutateAsync(formValues);
          targetLibraryId = created.id;
          setHighlightedId(created.id);
          setTimeout(() => setHighlightedId(null), 800);
        }

        await maybeReplaceLibraryTags({
          libraryId: targetLibraryId,
          normalizedTags,
          previousTagCount,
          isEditing: Boolean(editingLibrary),
        });

        showToast(editingLibrary ? t('libraries.toast.updated') : t('libraries.toast.created'));
        setIsFormOpen(false);
        setEditingLibrary(null);
        setEditingLibraryTags([]);
        setIsTagPrefillLoading(false);
      } catch (error) {
        console.error('Failed to save library:', error);
        const message = extractApiErrorMessage(error);
        showToast(t('libraries.toast.saveFailed', { message }));
      }
    };

    const maybeReplaceLibraryTags = async ({
      libraryId,
      normalizedTags,
      previousTagCount,
      isEditing,
    }: {
      libraryId: string;
      normalizedTags: LibraryFormTagValue[];
      previousTagCount: number;
      isEditing: boolean;
    }) => {
      const shouldPersist = isEditing ? previousTagCount > 0 || normalizedTags.length > 0 : normalizedTags.length > 0;
      if (!shouldPersist) return;

      const tagIds = await ensureTagIds(normalizedTags);
      await replaceLibraryTags(libraryId, tagIds, 25);
      queryClient.invalidateQueries({ queryKey: ['libraries'] });
      queryClient.invalidateQueries({ queryKey: ['libraries', libraryId] });
    };

    const ensureTagIds = async (tags: LibraryFormTagValue[]): Promise<string[]> => {
      const ids: string[] = [];
      for (const tag of tags) {
        if (tag.id) {
          ids.push(tag.id);
          continue;
        }
        const resolvedName = tag.name.trim();
        if (!resolvedName) continue;
        ids.push(await resolveTagId(resolvedName));
      }
      return ids;
    };

    const resolveTagId = async (name: string): Promise<string> => {
      try {
        const created = await createGlobalTag({ name, color: DEFAULT_TAG_COLOR });
        return created.id;
      } catch (error) {
        if (isConflictError(error)) {
          const matches = await searchGlobalTags({ keyword: name, limit: 5 });
          const exact = matches.find((tag) => tag.name.trim().toLowerCase() === name.trim().toLowerCase());
          if (exact) return exact.id;
        }
        throw error;
      }
    };

    const openCreateForm = () => {
      setEditingLibrary(null);
      setEditingLibraryTags([]);
      setIsTagPrefillLoading(false);
      setIsFormOpen(true);
    };

    const handleEditLibrary = (library: LibraryDto) => {
      setEditingLibrary(library);
      setEditingLibraryTags([]);
      setIsFormOpen(true);
    };

    // 提交搜索：更新 URL ?q= 触发数据刷新
    const commitSearch = () => {
      const trimmed = searchInput.trim();
      if (trimmed) {
        router.push(`/admin/libraries?q=${encodeURIComponent(trimmed)}`);
      } else {
        router.push('/admin/libraries');
      }
    };

    const handleSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        commitSearch();
      }
    };

    const [highlightedId, setHighlightedId] = useState<string | null>(null);

    // ESC 关闭
    useEffect(() => {
      const handler = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          setIsFormOpen(false);
          setEditingLibrary(null);
          setEditingLibraryTags([]);
          setIsTagPrefillLoading(false);
        }
      };
      window.addEventListener('keydown', handler);
      return () => window.removeEventListener('keydown', handler);
    }, []);

    useEffect(() => {
      setSearchInput(searchQuery);
    }, [searchQuery]);

    return (
      <div ref={ref} className={styles.widget}>
        <div className={styles.hero}>
          <div className={styles.heroRowTop}>
            <h2 className={styles.title}>{t('libraries.title')}</h2>
            <div className={styles.searchGroup}>
              <input
                className={styles.searchInput}
                placeholder={t('libraries.search.placeholder')}
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={handleSearchKey}
                aria-label={t('libraries.search.ariaLabel')}
              />
              <Button size="sm" variant="primary" onClick={openCreateForm}>
                {t('libraries.new')}
              </Button>
            </div>
          </div>
          <div className={styles.heroRowBottom}>
            <p className={styles.subtitle}>{t('libraries.subtitle')}</p>
            <div className={styles.controlsGroup}>
              <select
                className={styles.sortSelect}
                value={sortOption}
                onChange={handleSortChange}
                aria-label={t('libraries.sort.ariaLabel')}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {t(option.labelKey)}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className={styles.toggleButton}
                onClick={toggleArchived}
                aria-pressed={includeArchived}
              >
                {includeArchived ? t('libraries.archive.hide') : t('libraries.archive.show')}
              </button>
              <div className={styles.viewIcons}>
                <button
                  type="button"
                  aria-label={t('libraries.view.grid')}
                  className={`${styles.iconButton} ${viewMode === 'grid' ? styles.iconActive : ''}`}
                  onClick={() => toggleView('grid')}
                >
                  <LayoutGrid size={18} />
                </button>
                <button
                  type="button"
                  aria-label={t('libraries.view.list')}
                  className={`${styles.iconButton} ${viewMode === 'list' ? styles.iconActive : ''}`}
                  onClick={() => toggleView('list')}
                >
                  <ListIcon size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>
        <LibraryList
          onSelectLibrary={onSelectLibrary}
          onEditLibrary={handleEditLibrary}
          viewMode={viewMode}
          search={searchQuery}
          sort={sortOption}
          includeArchived={includeArchived}
          /* 仅在 grid 视图突出新建卡片 */
          highlightedLibraryId={viewMode === 'grid' ? highlightedId ?? undefined : undefined}
        />
        <LibraryForm
          isOpen={isFormOpen}
          mode={editingLibrary ? 'edit' : 'create'}
          initialValues={editingLibrary ? {
            name: editingLibrary.name,
            description: editingLibrary.description ?? '',
            theme_color: editingLibrary.theme_color ?? undefined,
          } : undefined}
          initialTags={editingLibrary ? editingLibraryTags : undefined}
          maxTags={TAG_LIMIT}
          onClose={() => {
            setIsFormOpen(false);
            setEditingLibrary(null);
            setEditingLibraryTags([]);
            setIsTagPrefillLoading(false);
          }}
          onSubmit={handleSaveLibrary}
          isLoading={editingLibrary ? quickUpdateMutation.isPending : createMutation.isPending}
          isTagPrefillLoading={isTagPrefillLoading}
        />
      </div>
    );
  }
);

LibraryMainWidget.displayName = 'LibraryMainWidget';

function normalizeTagSelections(tags: LibraryFormTagValue[] = []): LibraryFormTagValue[] {
  const normalized: LibraryFormTagValue[] = [];
  const seen = new Set<string>();
  for (const tag of tags) {
    const trimmed = (tag.name || '').trim();
    if (!trimmed) continue;
    const key = (tag.id || trimmed.toLowerCase());
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

function mapTagsResponseToFormValues(
  response: LibraryTagsResponseDto | undefined,
  untitledFallback: string,
): LibraryFormTagValue[] {
  if (!response) return [];
  const summaryMap = new Map(response.tags?.map((tag) => [tag.id, tag]) ?? []);
  return (response.tag_ids || []).map((id) => {
    const summary = summaryMap.get(id);
    return {
      id,
      name: summary?.name ?? untitledFallback,
      color: summary?.color || DEFAULT_TAG_COLOR,
    };
  });
}

function isConflictError(error: unknown): error is AxiosError<any> {
  const axiosError = error as AxiosError<any> | undefined;
  return Boolean(axiosError?.response && axiosError.response.status === 409);
}
