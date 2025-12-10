'use client';

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useState } from 'react';
import type { BookshelfDashboardItemDto } from '@/entities/bookshelf';
import { useQuickUpdateBookshelf } from '../model/hooks';
import { Button, Input, Modal } from '@/shared/ui';
import { showToast } from '@/shared/ui/toast';
import { useMostUsedTags, useTagSearch, useCreateTag } from '@/features/tag/model/hooks';
import { searchTags } from '@/features/tag/model/api';
import type { TagDto } from '@/entities/tag';
import styles from './BookshelfTagEditDialog.module.css';

interface BookshelfTagEditDialogProps {
  isOpen: boolean;
  bookshelf?: BookshelfDashboardItemDto | null;
  onClose: () => void;
  onSaved?: (payload: { bookshelfId: string; name: string; description?: string; tags: string[] }) => void;
}

const MAX_TAGS = 3;
const SUGGESTION_LIMIT = 8;

interface TagSelection {
  id?: string;
  name: string;
}

export const BookshelfTagEditDialog = ({
  isOpen,
  bookshelf,
  onClose,
  onSaved,
}: BookshelfTagEditDialogProps) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tagSelections, setTagSelections] = useState<TagSelection[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const quickUpdateMutation = useQuickUpdateBookshelf();
  const createTagMutation = useCreateTag();
  const isSaving = quickUpdateMutation.isPending || createTagMutation.isPending;

  useEffect(() => {
    if (isOpen && bookshelf) {
      setName(bookshelf.name ?? '');
      setDescription(bookshelf.description ?? '');
      setTagSelections(extractInitialSelections(bookshelf));
    } else {
      setName('');
      setDescription('');
      setTagSelections([]);
    }
    setTagInput('');
    setFormError(null);
  }, [isOpen, bookshelf?.id, bookshelf?.description]);

  const selectedNameKeys = useMemo(() => {
    return new Set(tagSelections.map((tag) => tag.name.toLowerCase()));
  }, [tagSelections]);

  const selectedIdKeys = useMemo(() => {
    const ids = tagSelections.map((tag) => tag.id).filter(Boolean) as string[];
    return new Set(ids);
  }, [tagSelections]);

  const canAddMore = tagSelections.length < MAX_TAGS;
  const debouncedQuery = useDebouncedValue(tagInput.trim(), 200);
  const isSearching = debouncedQuery.length > 0;

  const { data: searchResults = [], isFetching: searchLoading } = useTagSearch(debouncedQuery, {
    limit: SUGGESTION_LIMIT,
    enabled: isSearching,
  });

  const { data: popularTags = [], isFetching: popularLoading } = useMostUsedTags({
    limit: SUGGESTION_LIMIT,
    enabled: !isSearching,
  });

  const baseSuggestions = isSearching ? searchResults : popularTags;
  const filteredSuggestions = useMemo(() => {
    if (!Array.isArray(baseSuggestions)) return [] as TagDto[];
    return baseSuggestions
      .filter((tag) => {
        const trimmed = tag.name?.trim().toLowerCase();
        if (tag.id && selectedIdKeys.has(tag.id)) return false;
        if (trimmed && selectedNameKeys.has(trimmed)) return false;
        return Boolean(trimmed);
      })
      .slice(0, SUGGESTION_LIMIT);
  }, [baseSuggestions, selectedIdKeys, selectedNameKeys]);

  const statusLabel = isSearching ? '匹配' : '常用';

  const handleAddExistingTag = useCallback(
    (tag: TagDto) => {
      if (!canAddMore) return;
      const trimmed = (tag.name ?? '').trim();
      if (!trimmed) return;
      if (tag.id && selectedIdKeys.has(tag.id)) return;
      if (selectedNameKeys.has(trimmed.toLowerCase())) return;
      setTagSelections((prev) => [...prev, { id: tag.id ?? undefined, name: trimmed }]);
      setTagInput('');
    },
    [canAddMore, selectedIdKeys, selectedNameKeys],
  );

  const handleAddFreeTag = useCallback(
    (value: string) => {
      if (!canAddMore) return;
      const trimmed = value.trim();
      if (!trimmed) return;
      const key = trimmed.toLowerCase();
      if (selectedNameKeys.has(key)) return;
      setTagSelections((prev) => [...prev, { name: trimmed }]);
      setTagInput('');
    },
    [canAddMore, selectedNameKeys],
  );

  const handleRemoveTag = useCallback((index: number) => {
    setTagSelections((prev) => prev.filter((_, idx) => idx !== index));
  }, []);

  const resolveTagSelections = useCallback(
    async (items: TagSelection[]): Promise<Array<{ id: string; name: string }>> => {
      const resolved: Array<{ id: string; name: string }> = [];
      const seen = new Set<string>();

      for (const item of items) {
        const baseName = item.name.trim();
        if (!baseName) {
          continue;
        }
        const key = baseName.toLowerCase();
        if (seen.has(key)) {
          continue;
        }

        if (item.id) {
          resolved.push({ id: item.id, name: baseName });
          seen.add(key);
          continue;
        }

        const searchResults = await searchTags({ keyword: baseName, limit: 5 });
        const existing = searchResults.find(
          (tag) => tag.id && tag.name?.trim().toLowerCase() === key,
        );
        if (existing?.id) {
          resolved.push({ id: existing.id, name: existing.name });
          seen.add(key);
          continue;
        }

        const created = await createTagMutation.mutateAsync({
          name: baseName,
          color: generateTagColor(baseName),
        });
        resolved.push({ id: created.id, name: created.name });
        seen.add(key);
      }

      return resolved.slice(0, MAX_TAGS);
    },
    [createTagMutation],
  );

  const handleInputKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      handleAddFreeTag(tagInput);
    }
    if (event.key === 'Backspace' && !tagInput && tagSelections.length > 0) {
      event.preventDefault();
      setTagSelections((prev) => prev.slice(0, -1));
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!bookshelf) return;
    const trimmedName = name.trim();
    const trimmedDescription = description.trim();
    if (!trimmedName) {
      setFormError('名称不能为空');
      return;
    }
    try {
      const resolved = await resolveTagSelections(tagSelections);
      const tagIds = resolved.map((tag) => tag.id);
      const tagNames = resolved.map((tag) => tag.name);

      await quickUpdateMutation.mutateAsync({
        bookshelfId: bookshelf.id,
        data: {
          name: trimmedName,
          description: trimmedDescription ? trimmedDescription : undefined,
          tagIds,
        },
      });

      showToast('书橱标签已更新');
      onSaved?.({
        bookshelfId: bookshelf.id,
        name: trimmedName,
        description: trimmedDescription || undefined,
        tags: tagNames,
      });
      onClose();
    } catch (error) {
      const message = (error as Error)?.message || '保存失败';
      showToast(message);
      setFormError(message);
    }
  };

  const handleClose = () => {
    if (isSaving) return;
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      title="编辑书橱"
      subtitle="修改书橱名称与标签以便更快识别。"
      onClose={handleClose}
      closeOnBackdrop={false}
      showCloseButton
      lockScroll
      headingGap="compact"
    >
      <form className={styles.form} onSubmit={handleSubmit}>
        <Input
          label="书橱名称"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="输入书橱名称"
          required
          autoFocus
        />
        {formError && <span className={styles.errorText}>{formError}</span>}

        <div className={styles.descriptionField}>
          <label className={styles.descriptionLabel} htmlFor="bookshelf-description">
            简介（可选）
          </label>
          <textarea
            id="bookshelf-description"
            className={styles.descriptionTextarea}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="例如：记录日常学习的札记…"
            rows={3}
          />
          <span className={styles.helperText}>简介将展示在书橱卡片上，帮助运营团队快速了解用途。</span>
        </div>

        <div className={styles.fieldGroup}>
          <div className={styles.labelRow}>
            <span>标签</span>
            <span className={styles.limitNote}>最多 {MAX_TAGS} 个</span>
            {(searchLoading || popularLoading) && <span className={styles.limitNote}>加载中…</span>}
          </div>
          <div className={`${styles.tagInput} ${!canAddMore ? styles.tagInputFull : ''}`}>
            {tagSelections.map((tag, index) => (
              <span key={`${tag.id ?? tag.name}-${index}`} className={styles.tagChip}>
                {tag.name}
                <button
                  type="button"
                  className={styles.tagRemoveButton}
                  onClick={() => handleRemoveTag(index)}
                  aria-label={`移除标签 ${tag.name}`}
                >
                  ×
                </button>
              </span>
            ))}
            <input
              className={styles.tagInputField}
              type="text"
              placeholder={canAddMore ? '输入标签并回车…' : '已达到上限'}
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              disabled={!canAddMore || isSaving}
            />
          </div>
          <p className={styles.helperText}>标签会展示在书橱卡片上，帮助运营团队快速筛选。</p>
          {canAddMore && filteredSuggestions.length > 0 && (
            <div className={styles.suggestions}>
              {filteredSuggestions.map((tag) => (
                <button
                  type="button"
                  key={tag.id ?? tag.name}
                  className={styles.suggestionButton}
                  onClick={() => handleAddExistingTag(tag)}
                >
                  <span>{tag.name}</span>
                  <span className={styles.suggestionMeta}>{statusLabel}</span>
                </button>
              ))}
            </div>
          )}
          {canAddMore && filteredSuggestions.length === 0 && (debouncedQuery || !isSearching) && (
            <p className={styles.emptySuggestions}>没有更多可用的标签，输入后按回车即可新建。</p>
          )}
          {!canAddMore && <p className={styles.helperText}>已选择 {MAX_TAGS} 个标签。</p>}
        </div>

        <div className={styles.footer}>
          <Button type="submit" variant="primary" loading={isSaving} disabled={!bookshelf}>
            保存
          </Button>
        </div>
      </form>
    </Modal>
  );
};

BookshelfTagEditDialog.displayName = 'BookshelfTagEditDialog';

function extractInitialSelections(item?: BookshelfDashboardItemDto | null): TagSelection[] {
  if (!item) return [];
  const ids = Array.isArray(item.tagIds)
    ? item.tagIds
    : Array.isArray((item as any)?.tag_ids)
      ? ((item as any)?.tag_ids as string[])
      : [];
  const names = Array.isArray((item as any)?.tagsSummary)
    ? ((item as any)?.tagsSummary as string[])
    : Array.isArray((item as any)?.tagsMeta)
      ? ((item as any)?.tagsMeta as Array<{ name: string }>).map((tag) => tag.name)
      : Array.isArray((item as any)?.tags_summary)
        ? ((item as any)?.tags_summary as string[])
        : Array.isArray((item as any)?.tags)
          ? ((item as any)?.tags as string[])
          : [];

  const selections: TagSelection[] = [];
  const seen = new Set<string>();
  const max = Math.max(ids.length, names.length);

  for (let index = 0; index < max; index += 1) {
    const id = ids[index];
    const rawName = (names[index] ?? '').trim();
    const fallbackName = rawName || id || '';
    if (!fallbackName) {
      continue;
    }
    const key = fallbackName.toLowerCase();
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    selections.push({
      id,
      name: rawName || fallbackName,
    });
    if (selections.length >= MAX_TAGS) {
      break;
    }
  }

  return selections;
}

function useDebouncedValue<T>(value: T, delay: number): T {
  const [current, setCurrent] = useState(value);
  useEffect(() => {
    const handle = setTimeout(() => setCurrent(value), delay);
    return () => clearTimeout(handle);
  }, [value, delay]);
  return current;
}

const TAG_COLOR_PALETTE = ['#6366F1', '#0EA5E9', '#10B981', '#F97316', '#F59E0B', '#EF4444', '#8B5CF6'];

function generateTagColor(seed: string): string {
  const normalized = seed.trim().toLowerCase() || 'tag';
  let hash = 0;
  for (let i = 0; i < normalized.length; i += 1) {
    hash = (hash * 31 + normalized.charCodeAt(i)) >>> 0;
  }
  return TAG_COLOR_PALETTE[hash % TAG_COLOR_PALETTE.length];
}
