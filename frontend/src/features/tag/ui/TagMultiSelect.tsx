import React from 'react';
import type { TagDto } from '@/entities/tag';
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
    label = '标签',
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
  const inputDisabled = disabled || !canAddMore;
  const resolvedPlaceholder = placeholder ?? (canAddMore ? '输入标签并回车…' : '已达到上限');

  return (
    <div className={styles.container}>
      <div className={styles.labelRow}>
        <span>{label}</span>
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
              aria-label={`移除标签 ${tag.name}`}
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
          <p className={styles.loadingText}>加载标签…</p>
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
        <p className={styles.helperText}>
          已选择 {selections.length}
          {typeof maxTags === 'number' ? `/${maxTags}` : ''} 个标签
        </p>
      )}
    </div>
  );
}
