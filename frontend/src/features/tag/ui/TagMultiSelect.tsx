'use client';

import React from 'react';
import type { TagDto } from '@/entities/tag';
import { useI18n } from '@/i18n/useI18n';
import styles from './TagMultiSelect.module.css';

export interface TagMultiSelectProps<Chip extends { id?: string; name: string }> {
  label?: React.ReactNode;
  limitNote?: string;
  helperText?: string;
  maxTags?: number;
  canAddMore: boolean;
  selections: Chip[];
  inputValue: string;
  placeholder?: string;
  disabled?: boolean;
  statusText?: string;
  suggestions: TagDto[];
  suggestionsLabel: string;
  suggestionsLoading?: boolean;
  suggestionEmptyMessage?: string;
  onInputChange: (value: string) => void;
  onInputKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onRemoveTag: (index: number) => void;
  onSelectSuggestion: (tag: TagDto) => void;
}

export function TagMultiSelect<Chip extends { id?: string; name: string }>(
  {
    label,
    limitNote,
    maxTags,
    helperText,
    canAddMore,
    selections,
    inputValue,
    placeholder,
    disabled,
    statusText,
    suggestions,
    suggestionsLabel,
    suggestionsLoading,
    suggestionEmptyMessage,
    onInputChange,
    onInputKeyDown,
    onRemoveTag,
    onSelectSuggestion,
  }: TagMultiSelectProps<Chip>,
) {
  const { t } = useI18n();
  const inputDisabled = disabled || !canAddMore;
  const resolvedLabel = label ?? t('tags.multiSelect.label');
  const resolvedPlaceholder = placeholder
    ?? (canAddMore ? t('tags.multiSelect.placeholder') : t('tags.multiSelect.placeholderLimit'));
  const selectedSummary = typeof maxTags === 'number'
    ? t('tags.multiSelect.selectedWithMax', { count: selections.length, max: maxTags })
    : t('tags.multiSelect.selected', { count: selections.length });

  return (
    <div className={styles.container}>
      <div className={styles.labelRow}>
        <span>{resolvedLabel}</span>
        {limitNote && <span className={styles.limitNote}>{limitNote}</span>}
        {statusText && <span className={styles.statusText}>{statusText}</span>}
      </div>
      <div
        className={[
          styles.inputShell,
          inputDisabled ? styles.inputShellDisabled : '',
          !canAddMore ? styles.inputShellFull : '',
        ].filter(Boolean).join(' ')}
      >
        {selections.map((tag, index) => (
          <span key={`${tag.id ?? tag.name}-${index}`} className={styles.chip}>
            {tag.name}
            <button
              type="button"
              className={styles.chipRemoveButton}
              onClick={() => onRemoveTag(index)}
              aria-label={t('tags.multiSelect.removeAria', { name: tag.name })}
            >
              ×
            </button>
          </span>
        ))}
        <input
          className={styles.inputField}
          type="text"
          value={inputValue}
          placeholder={resolvedPlaceholder}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={onInputKeyDown}
          disabled={inputDisabled}
        />
      </div>
      {helperText && <p className={styles.helperText}>{helperText}</p>}
      {canAddMore ? (
        suggestionsLoading ? (
          <p className={styles.loadingText}>{t('tags.multiSelect.loading')}</p>
        ) : suggestions.length === 0 ? (
          suggestionEmptyMessage ? (
            <p className={styles.emptySuggestions}>{suggestionEmptyMessage}</p>
          ) : null
        ) : (
          <div className={styles.suggestions}>
            {suggestions.map((tag) => (
              <button
                type="button"
                key={tag.id ?? tag.name}
                className={styles.suggestionButton}
                onClick={() => onSelectSuggestion(tag)}
              >
                <span>{tag.name}</span>
                <span className={styles.suggestionMeta}>{suggestionsLabel}</span>
              </button>
            ))}
          </div>
        )
      ) : (
        <p className={styles.helperText}>{selectedSummary}</p>
      )}
    </div>
  );
}
