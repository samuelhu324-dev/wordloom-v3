import { useCallback, useEffect, useMemo, useState } from 'react';
import type { BookDto, BookCoverIconId } from '@/entities/book';
import { MAX_TAGS, type DialogMode, type TagSelection } from '../types';
import { extractInitialSelections } from '../utils';

interface UseBookEditStateParams {
  isOpen: boolean;
  mode: DialogMode;
  book?: BookDto | null;
}

export const useBookEditState = ({ isOpen, mode, book }: UseBookEditStateParams) => {
  const isEditMode = mode === 'edit';
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [tagSelections, setTagSelections] = useState<TagSelection[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [coverIconId, setCoverIconId] = useState<BookCoverIconId | null>(null);

  const resetCoreFields = useCallback(() => {
    setTitle('');
    setSummary('');
    setTagSelections([]);
    setCoverIconId(null);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      resetCoreFields();
      setTagInput('');
      return;
    }

    if (isEditMode && book) {
      setTitle(book.title ?? '');
      setSummary(book.summary ?? '');
      const initialSelections = extractInitialSelections(book);
      setTagSelections(initialSelections);
      setCoverIconId(book.coverIconId ?? null);
    } else {
      resetCoreFields();
    }

    setTagInput('');
  }, [book, isEditMode, isOpen, resetCoreFields]);

  const selectedNameKeys = useMemo(() => new Set(tagSelections.map((tag) => tag.name.toLowerCase())), [tagSelections]);
  const canAddMore = tagSelections.length < MAX_TAGS;

  return {
    fields: {
      title,
      summary,
      coverIconId,
      tagSelections,
      tagInput,
    },
    setTitle,
    setSummary,
    setCoverIconId,
    setTagSelections,
    setTagInput,
    canAddMore,
    selectedNameKeys,
  };
};
