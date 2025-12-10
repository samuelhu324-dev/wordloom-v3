'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { CreateLibraryRequest } from '@/entities/library';
import type { TagDto } from '@/entities/tag';
import { Button, Input, Modal } from '@/shared/ui';
import { TagMultiSelect } from '@/features/tag/ui';
import { useTagSuggestions } from '@/features/tag/model/useTagSuggestions';
import { DEFAULT_LIBRARY_THEME_COLOR, DEFAULT_TAG_COLOR } from '../constants';
import { useI18n } from '@/i18n/useI18n';

export interface LibraryFormTagValue {
  id?: string;
  name: string;
  color?: string;
  isNew?: boolean;
}

export interface LibraryFormSubmitPayload {
  formValues: CreateLibraryRequest;
  tags: LibraryFormTagValue[];
}

export interface LibraryFormProps {
  isOpen: boolean;
  mode?: 'create' | 'edit';
  initialValues?: Partial<CreateLibraryRequest>;
  initialTags?: LibraryFormTagValue[];
  maxTags?: number;
  onClose: () => void;
  onSubmit: (payload: LibraryFormSubmitPayload) => Promise<void> | void;
  isLoading?: boolean;
  isTagPrefillLoading?: boolean;
  createTitle?: string;
  editTitle?: string;
  createSubtitle?: string;
  editSubtitle?: string;
  nameLabel?: string;
  namePlaceholder?: string;
  descriptionLabel?: string;
  descriptionPlaceholder?: string;
  createSubmitLabel?: string;
  editSubmitLabel?: string;
  showThemeColorField?: boolean;
}

export const LibraryForm: React.FC<LibraryFormProps> = ({
  isOpen,
  mode = 'create',
  initialValues,
  initialTags,
  maxTags = 3,
  onClose,
  onSubmit,
  isLoading,
  isTagPrefillLoading,
  createTitle,
  editTitle,
  createSubtitle,
  editSubtitle,
  nameLabel,
  namePlaceholder,
  descriptionLabel,
  descriptionPlaceholder,
  createSubmitLabel,
  editSubmitLabel,
  showThemeColorField = true,
}) => {
  const { t } = useI18n();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedTags, setSelectedTags] = useState<LibraryFormTagValue[]>(initialTags ?? []);
  const [tagInput, setTagInput] = useState('');
  const initialThemeColorValue = useMemo(() => {
    if (mode === 'edit') {
      return initialValues?.theme_color ?? '';
    }
    const provided = initialValues?.theme_color?.trim();
    if (provided) {
      return provided;
    }
    return DEFAULT_LIBRARY_THEME_COLOR;
  }, [initialValues?.theme_color, mode]);
  const [themeColor, setThemeColor] = useState(initialThemeColorValue);

  useEffect(() => {
    if (!isOpen) return;
    setName(initialValues?.name ?? '');
    setDescription(initialValues?.description ?? '');
    setThemeColor(initialThemeColorValue);
    setTagInput('');
  }, [isOpen, initialValues?.name, initialValues?.description, initialThemeColorValue]);

  useEffect(() => {
    if (!isOpen) return;
    setSelectedTags(initialTags ?? []);
    setTagInput('');
  }, [isOpen, initialTags]);

  const selectedNameKeys = useMemo(() => {
    const entries = selectedTags.map((tag) => tag.name?.trim().toLowerCase()).filter(Boolean) as string[];
    return new Set(entries);
  }, [selectedTags]);

  const { items, label: suggestionLabel, isLoading: suggestionsLoading, query, isSearching } = useTagSuggestions(tagInput, {
    isOpen,
  });
  const tagEmptyHint = t('libraries.form.tags.emptyHint');

  const filteredSuggestions = useMemo(() => {
    return (items ?? []).filter((tag) => {
      const trimmed = tag.name?.trim().toLowerCase();
      if (!trimmed) return false;
      return !selectedNameKeys.has(trimmed);
    });
  }, [items, selectedNameKeys]);

  const suggestionEmptyMessage = useMemo(() => {
    const noSuggestions = filteredSuggestions.length === 0;
    if (!noSuggestions) return undefined;
    if (!maxTags || selectedTags.length < maxTags) {
      if (query || !isSearching) {
        return tagEmptyHint;
      }
    }
    return undefined;
  }, [filteredSuggestions.length, selectedTags.length, maxTags, query, isSearching, tagEmptyHint]);

  const canAddMoreTags = selectedTags.length < maxTags;
  const trimmedThemeColor = themeColor.trim();
  const themeColorError = useMemo(() => {
    if (!trimmedThemeColor) return undefined;
    return /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(trimmedThemeColor)
      ? undefined
      : t('libraries.form.theme.error');
  }, [trimmedThemeColor, t]);
  const resolvedThemeColorValue = themeColorError ? '' : trimmedThemeColor;
  const colorPickerValue = resolvedThemeColorValue && resolvedThemeColorValue.length === 7
    ? resolvedThemeColorValue
    : DEFAULT_LIBRARY_THEME_COLOR;
  const resolvedCreateTitle = createTitle ?? t('libraries.form.title.create');
  const resolvedEditTitle = editTitle ?? t('libraries.form.title.edit');
  const resolvedCreateSubtitle = createSubtitle ?? t('libraries.form.subtitle.create');
  const resolvedEditSubtitle = editSubtitle ?? t('libraries.form.subtitle.edit');
  const resolvedNameLabel = nameLabel ?? t('libraries.form.name.label');
  const resolvedNamePlaceholder = namePlaceholder ?? t('libraries.form.name.placeholder');
  const resolvedDescriptionLabel = descriptionLabel ?? t('libraries.form.description.label');
  const resolvedDescriptionPlaceholder = descriptionPlaceholder ?? t('libraries.form.description.placeholder');
  const resolvedTagLabel = t('libraries.form.tags.label');
  const tagLimitNote = t('libraries.form.tags.limitNote', { max: maxTags });
  const tagHelperText = t('libraries.form.tags.helper');
  const themeLabel = t('libraries.form.theme.label');
  const themePickerTitle = t('libraries.form.theme.pickerTitle');
  const themeAriaLabel = t('libraries.form.theme.ariaLabel');
  const themePlaceholder = t('libraries.form.theme.placeholder', { defaultColor: DEFAULT_LIBRARY_THEME_COLOR.toUpperCase() });
  const themeHelper = t('libraries.form.theme.helper');

  const handleAddExistingTag = (tag: TagDto) => {
    if (!canAddMoreTags) return;
    const trimmed = (tag.name ?? '').trim();
    if (!trimmed) return;
    const key = trimmed.toLowerCase();
    if (selectedNameKeys.has(key)) return;
    setSelectedTags((prev) => [...prev, { id: tag.id, name: trimmed, color: tag.color || DEFAULT_TAG_COLOR }]);
    setTagInput('');
  };

  const handleAddFreeTag = (value: string) => {
    if (!canAddMoreTags) return;
    const trimmed = value.trim();
    if (!trimmed) return;
    const key = trimmed.toLowerCase();
    if (selectedNameKeys.has(key)) return;
    setSelectedTags((prev) => [...prev, { name: trimmed }]);
    setTagInput('');
  };

  const handleRemoveTag = (index: number) => {
    setSelectedTags((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleTagInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      handleAddFreeTag(tagInput);
    }
    if (event.key === 'Backspace' && !tagInput && selectedTags.length > 0) {
      event.preventDefault();
      setSelectedTags((prev) => prev.slice(0, -1));
    }
  };

  const isEdit = mode === 'edit';
  const resolvedTitle = isEdit ? resolvedEditTitle : resolvedCreateTitle;
  const resolvedSubtitle = isEdit ? resolvedEditSubtitle : resolvedCreateSubtitle;
  const resolvedSubmitLabel = isEdit
    ? (editSubmitLabel ?? t('button.save'))
    : (createSubmitLabel ?? t('button.create'));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    const trimmedDesc = description.trim();
    if (!trimmedName) return;
    if (themeColorError) return;
    await Promise.resolve(
      onSubmit({
        formValues: {
          name: trimmedName,
          description: trimmedDesc ? trimmedDesc : undefined,
          theme_color: showThemeColorField ? (resolvedThemeColorValue || undefined) : undefined,
        },
        tags: selectedTags,
      })
    );
    if (!isEdit) {
      setName('');
      setDescription('');
      setSelectedTags([]);
      setTagInput('');
      setThemeColor('');
    }
  };

  const statusText = isTagPrefillLoading
    ? t('libraries.form.tags.status.prefill')
    : (suggestionsLoading || isSearching)
      ? t('libraries.form.tags.status.search')
      : undefined;

  return (
    <Modal
      isOpen={isOpen}
      title={resolvedTitle}
      subtitle={resolvedSubtitle}
      onClose={onClose}
      closeOnBackdrop={false}
      showCloseButton
      lockScroll
      headingGap="compact"
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        <Input
          label={resolvedNameLabel}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={resolvedNamePlaceholder}
          required
          autoFocus
        />
        <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
          <label style={{ fontSize:'var(--font-size-xs)', fontWeight:500, letterSpacing:'.5px' }}>{resolvedDescriptionLabel}</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={resolvedDescriptionPlaceholder}
            rows={3}
            style={{
              resize:'vertical',
              padding:'8px 10px',
              fontFamily:'inherit',
              fontSize:'var(--font-size-sm)',
              lineHeight:1.5,
              border:'1px solid var(--color-border-soft)',
              borderRadius:'var(--radius-sm)',
              background:'var(--color-surface-alt)',
              color:'var(--color-text-primary)'
            }}
          />
        </div>
        <TagMultiSelect
          label={resolvedTagLabel}
          limitNote={tagLimitNote}
          maxTags={maxTags}
          helperText={tagHelperText}
          canAddMore={canAddMoreTags}
          selections={selectedTags}
          inputValue={tagInput}
          disabled={Boolean(isLoading)}
          statusText={statusText}
          suggestions={filteredSuggestions}
          suggestionsLabel={suggestionLabel}
          suggestionsLoading={suggestionsLoading}
          suggestionEmptyMessage={suggestionEmptyMessage}
          onInputChange={setTagInput}
          onInputKeyDown={handleTagInputKeyDown}
          onRemoveTag={handleRemoveTag}
          onSelectSuggestion={handleAddExistingTag}
        />
        {showThemeColorField && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, letterSpacing: '0.4px', textTransform: 'uppercase', color: 'var(--color-text-secondary)' }}>
                {themeLabel}
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="color"
                  value={colorPickerValue}
                  onChange={(event) => {
                    setThemeColor(event.target.value);
                  }}
                  title={themePickerTitle}
                  style={{ width: 32, height: 32, border: 'none', background: 'transparent', cursor: 'pointer' }}
                />
                <Input
                  label={undefined}
                  aria-label={themeAriaLabel}
                  value={themeColor}
                  onChange={(event) => setThemeColor(event.target.value)}
                  placeholder={themePlaceholder}
                />
              </div>
            </div>
            <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: themeColorError ? 'var(--color-text-danger)' : 'var(--color-text-tertiary)' }}>
              {themeColorError ?? themeHelper}
            </p>
          </div>
        )}
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', justifyContent: 'flex-end', marginTop: 'var(--spacing-xs)' }}>
          <Button type="submit" variant="primary" loading={isLoading}>
            {resolvedSubmitLabel}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
