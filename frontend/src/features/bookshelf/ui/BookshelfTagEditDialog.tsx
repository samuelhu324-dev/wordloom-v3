'use client';

import { FormEvent, KeyboardEvent, useCallback, useEffect, useId, useMemo, useState } from 'react';
import type { BookshelfDashboardItemDto } from '@/entities/bookshelf';
import { useQuickUpdateBookshelf } from '../model/hooks';
import { Button, Input, Modal } from '@/shared/ui';
import { showToast } from '@/shared/ui/toast';
import { useMostUsedTags, useTagSearch, useCreateTag } from '@/features/tag/model/hooks';
import { searchTags } from '@/features/tag/model/api';
import type { TagDto } from '@/entities/tag';
import { TagMultiSelect } from '@/features/tag/ui';
import { useI18n } from '@/i18n/useI18n';
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
  const { t } = useI18n();
  const formId = useId();
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

  const statusLabel = isSearching
    ? t('bookshelves.tags.dialog.status.matching')
    : t('bookshelves.tags.dialog.status.popular');

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
      setFormError(t('bookshelves.tags.dialog.errorRequired'));
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

      showToast(t('bookshelves.tags.dialog.toastSuccess'));
      onSaved?.({
        bookshelfId: bookshelf.id,
        name: trimmedName,
        description: trimmedDescription || undefined,
        tags: tagNames,
      });
      onClose();
    } catch (error) {
      const fallbackMessage = t('bookshelves.tags.dialog.errorGeneric');
      const message = (error as Error)?.message || fallbackMessage;
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
      title={t('bookshelves.tags.dialog.title')}
      subtitle={t('bookshelves.tags.dialog.subtitle')}
      onClose={handleClose}
      closeOnBackdrop={false}
      showCloseButton
      lockScroll
      headingGap="compact"
      footer={(
        <div className={styles.footer}>
          <Button type="submit" variant="primary" loading={isSaving} disabled={!bookshelf} form={formId}>
            {t('button.save')}
          </Button>
        </div>
      )}
    >
      <form id={formId} className={styles.form} onSubmit={handleSubmit}>
        <Input
          label={t('bookshelves.tags.dialog.nameLabel')}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('bookshelves.tags.dialog.namePlaceholder')}
          required
          autoFocus
        />
        {formError && <span className={styles.errorText}>{formError}</span>}

        <div className={styles.descriptionField}>
          <label className={styles.descriptionLabel} htmlFor="bookshelf-description">
            {t('bookshelves.tags.dialog.descriptionLabel')}
          </label>
          <textarea
            id="bookshelf-description"
            className={styles.descriptionTextarea}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder={t('bookshelves.tags.dialog.descriptionPlaceholder')}
            rows={3}
          />
          <span className={styles.helperText}>{t('bookshelves.tags.dialog.descriptionHelper')}</span>
        </div>
        <TagMultiSelect
          label={t('bookshelves.tags.dialog.fieldLabel')}
          limitNote={t('bookshelves.tags.dialog.limitNote', { max: MAX_TAGS })}
          helperText={t('bookshelves.tags.dialog.helper')}
          maxTags={MAX_TAGS}
          canAddMore={canAddMore}
          selections={tagSelections}
          inputValue={tagInput}
          disabled={isSaving}
          statusText={(searchLoading || popularLoading) ? t('bookshelves.tags.dialog.loading') : undefined}
          suggestions={filteredSuggestions}
          suggestionsLabel={statusLabel}
          suggestionsLoading={searchLoading || popularLoading}
          suggestionEmptyMessage={canAddMore && (debouncedQuery || !isSearching)
            ? t('bookshelves.tags.dialog.emptySuggestions')
            : undefined}
          onInputChange={(value) => setTagInput(value)}
          onInputKeyDown={handleInputKeyDown}
          onRemoveTag={handleRemoveTag}
          onSelectSuggestion={handleAddExistingTag}
        />
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
