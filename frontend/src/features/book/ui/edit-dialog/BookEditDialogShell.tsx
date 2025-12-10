"use client";

import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { BookDto } from '@/entities/book';
import { useCreateBook, useUpdateBook } from '@/features/book/model/hooks';
import { updateBook as updateBookApi } from '@/features/book/model/api';
import { showToast } from '@/shared/ui/toast';
import { Modal } from '@/shared/ui';
import { useCreateTag } from '@/features/tag/model/hooks';
import { searchTags } from '@/features/tag/model/api';
import type { TagDto } from '@/entities/tag';
import { BookEditForm } from './BookEditForm';
import { useTagSuggestions } from './hooks/useTagSuggestions';
import { useBookEditState } from './hooks/useBookEditState';
import { generateTagColor } from './utils';
import { TAG_SUGGESTION_LIMIT } from '@/features/tag/constants';
import {
  MAX_TAGS,
  type DialogMode,
  type TagSelection,
} from './types';
import { useI18n } from '@/i18n/useI18n';

export interface BookEditDialogShellProps {
  isOpen: boolean;
  mode?: DialogMode;
  book?: BookDto | null;
  bookshelfId?: string;
  libraryId?: string;
  onClose: () => void;
  onSaved?: (payload: { bookId: string; title: string; summary?: string; tags: string[] }) => void;
  onCreated?: (payload: { book: BookDto }) => void;
  onPendingChange?: (pending: boolean) => void;
}

export const BookEditDialogShell = ({
  isOpen,
  mode = 'edit',
  book,
  bookshelfId,
  libraryId,
  onClose,
  onSaved,
  onCreated,
  onPendingChange,
}: BookEditDialogShellProps) => {
  const { t } = useI18n();
  const isEditMode = mode === 'edit';
  const queryClient = useQueryClient();
  const updateBookMutation = useUpdateBook(book?.id ?? '');
  const createBookMutation = useCreateBook();
  const createTagMutation = useCreateTag();
  const [formError, setFormError] = useState<string | null>(null);
  const [isSyncingTags, setIsSyncingTags] = useState(false);

  const {
    fields: { title, summary, coverIconId, tagSelections, tagInput },
    setTitle,
    setSummary,
    setCoverIconId,
    setTagInput,
    setTagSelections,
    canAddMore,
    selectedNameKeys,
  } = useBookEditState({ isOpen, mode, book });

  const { items, label, isLoading, query, isSearching } = useTagSuggestions(tagInput, { isOpen });
  const tagEmptyHint = t('books.dialog.tags.emptyHint');

  const filteredSuggestions = useMemo(() => {
    const base = Array.isArray(items) ? items : [];
    return base
      .filter((tag) => {
        const trimmed = tag.name?.trim().toLowerCase();
        if (!trimmed) return false;
        if (selectedNameKeys.has(trimmed)) return false;
        return true;
      })
      .slice(0, TAG_SUGGESTION_LIMIT);
  }, [items, selectedNameKeys]);

  const handleAddExistingTag = useCallback(
    (tag: TagDto) => {
      if (!canAddMore) return;
      const trimmed = (tag.name ?? '').trim();
      if (!trimmed) return;
      const key = trimmed.toLowerCase();
      if (selectedNameKeys.has(key)) return;
      setTagSelections((prev) => [...prev, { id: tag.id ?? undefined, name: trimmed }]);
      setTagInput('');
    },
    [canAddMore, selectedNameKeys, setTagSelections, setTagInput],
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
    [canAddMore, selectedNameKeys, setTagSelections, setTagInput],
  );

  const handleRemoveTag = useCallback((index: number) => {
    setTagSelections((prev) => prev.filter((_, idx) => idx !== index));
  }, [setTagSelections]);

  const handleTagInputKeyDown = useCallback(
    (event: KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        handleAddFreeTag(tagInput);
      }
      if (event.key === 'Backspace' && !tagInput && tagSelections.length > 0) {
        event.preventDefault();
        setTagSelections((prev) => prev.slice(0, -1));
      }
    },
    [handleAddFreeTag, setTagSelections, tagInput, tagSelections.length],
  );

  const resolveTagSelections = useCallback(
    async (itemsToResolve: TagSelection[]): Promise<Array<{ id: string; name: string }>> => {
      const resolved: Array<{ id: string; name: string }> = [];
      const seen = new Set<string>();

      for (const item of itemsToResolve) {
        const baseName = item.name.trim();
        if (!baseName) continue;
        const key = baseName.toLowerCase();
        if (seen.has(key)) continue;

        if (item.id) {
          resolved.push({ id: item.id, name: baseName });
          seen.add(key);
          continue;
        }

        const searchCandidates = await searchTags({ keyword: baseName, limit: 5 });
        const existing = searchCandidates.find((tag) => tag.id && tag.name?.trim().toLowerCase() === key);
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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedTitle = title.trim();
    const trimmedSummary = summary.trim();

    if (!trimmedTitle) {
      setFormError(t('books.dialog.errors.titleRequired'));
      return;
    }

    try {
      setFormError(null);
      setIsSyncingTags(true);
      const resolvedCurrent = await resolveTagSelections(tagSelections);
      const tagIdsPayload = resolvedCurrent.map((tag) => tag.id);

      if (isEditMode) {
        if (!book) {
          setFormError(t('books.dialog.errors.bookLoading'));
          return;
        }

        await updateBookMutation.mutateAsync({
          title: trimmedTitle,
          summary: trimmedSummary ? trimmedSummary : undefined,
          tag_ids: tagIdsPayload,
          cover_icon: coverIconId ?? null,
        });

        await queryClient.invalidateQueries({ queryKey: ['books'] });
        await queryClient.invalidateQueries({ queryKey: ['books', book.id] });

        showToast(t('books.dialog.toast.updated'));
        onSaved?.({
          bookId: book.id,
          title: trimmedTitle,
          summary: trimmedSummary || undefined,
          tags: resolvedCurrent.map((tag) => tag.name),
        });
        onClose();
      } else {
        if (!bookshelfId || !libraryId) {
          setFormError(t('books.dialog.errors.missingBookshelf'));
          return;
        }

        const createdBook = await createBookMutation.mutateAsync({
          bookshelf_id: bookshelfId,
          library_id: libraryId,
          title: trimmedTitle,
          summary: trimmedSummary ? trimmedSummary : undefined,
          cover_icon: coverIconId ?? null,
        });

        if (tagIdsPayload.length > 0) {
          try {
            await updateBookApi(createdBook.id, { tag_ids: tagIdsPayload });
          } catch (tagError) {
            console.error('[BookEditDialog] tag sync after create failed', tagError);
            showToast(t('books.dialog.toast.tagSyncFailed'));
          }
        }

        await queryClient.invalidateQueries({ queryKey: ['books'] });
        await queryClient.invalidateQueries({ queryKey: ['books', createdBook.id] });

        showToast(t('books.dialog.toast.created'));
        onCreated?.({ book: createdBook });
        onClose();
      }
    } catch (error) {
      console.error('[BookEditDialog] 保存失败', error);
      const fallbackMessage = t('books.dialog.errors.saveFailed');
      const message = (error as Error)?.message || fallbackMessage;
      showToast(message);
      setFormError(message);
    } finally {
      setIsSyncingTags(false);
    }
  };

  const isSaving =
    isSyncingTags || updateBookMutation.isPending || createTagMutation.isPending || createBookMutation.isPending;

  useEffect(() => {
    onPendingChange?.(isSaving);
  }, [isSaving, onPendingChange]);

  const handleClose = () => {
    if (isSaving) return;
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      title={isEditMode ? t('books.dialog.title.edit') : t('books.dialog.title.create')}
      onClose={handleClose}
      closeOnBackdrop={false}
      showCloseButton
      lockScroll
      headingGap="compact"
    >
      <BookEditForm
        mode={mode}
        title={title}
        summary={summary}
        coverIconId={coverIconId}
        tagSelections={tagSelections}
        tagInput={tagInput}
        canAddMoreTags={canAddMore}
        suggestions={filteredSuggestions}
        suggestionLabel={label}
        suggestionsLoading={isLoading}
        suggestionEmptyMessage={
          canAddMore && filteredSuggestions.length === 0 && (query || !isSearching)
            ? tagEmptyHint
            : undefined
        }
        isSaving={isSaving}
        formError={formError}
        submitDisabled={isEditMode ? !book : false}
        onSubmit={handleSubmit}
        onTitleChange={setTitle}
        onSummaryChange={setSummary}
        onCoverIconChange={setCoverIconId}
        onTagInputChange={setTagInput}
        onTagInputKeyDown={handleTagInputKeyDown}
        onRemoveTag={handleRemoveTag}
        onSelectSuggestion={handleAddExistingTag}
      />
    </Modal>
  );
};

BookEditDialogShell.displayName = 'BookEditDialog';
