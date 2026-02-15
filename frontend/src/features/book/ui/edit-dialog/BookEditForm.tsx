import React, { FormEvent, KeyboardEvent } from 'react';
import type { BookCoverIconId } from '@/entities/book';
import type { TagDto } from '@/entities/tag';
import { Input } from '@/shared/ui';
import styles from '../BookEditDialog.module.css';
import type { DialogMode, TagSelection } from './types';
import { MAX_TAGS } from './types';
import { CoverIconSelector } from './CoverIconSelector';
import { TagMultiSelect } from '@/features/tag/ui';
import { useI18n } from '@/i18n/useI18n';

interface BookEditFormProps {
  formId?: string;
  mode: DialogMode;
  title: string;
  summary: string;
  coverIconId: BookCoverIconId | null;
  tagSelections: TagSelection[];
  tagInput: string;
  canAddMoreTags: boolean;
  suggestions: TagDto[];
  suggestionLabel: string;
  suggestionsLoading: boolean;
  suggestionEmptyMessage?: string;
  isSaving: boolean;
  formError: string | null;
  submitDisabled?: boolean;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTitleChange: (value: string) => void;
  onSummaryChange: (value: string) => void;
  onCoverIconChange: (value: BookCoverIconId | null) => void;
  onTagInputChange: (value: string) => void;
  onTagInputKeyDown: (event: KeyboardEvent<HTMLInputElement>) => void;
  onRemoveTag: (index: number) => void;
  onSelectSuggestion: (tag: TagDto) => void;
}

export const BookEditForm: React.FC<BookEditFormProps> = ({
  formId,
  mode,
  title,
  summary,
  coverIconId,
  tagSelections,
  tagInput,
  canAddMoreTags,
  suggestions,
  suggestionLabel,
  suggestionsLoading,
  suggestionEmptyMessage,
  isSaving,
  formError,
  submitDisabled = false,
  onSubmit,
  onTitleChange,
  onSummaryChange,
  onCoverIconChange,
  onTagInputChange,
  onTagInputKeyDown,
  onRemoveTag,
  onSelectSuggestion,
}) => {
  const { t } = useI18n();

  return (
    <form id={formId} className={styles.form} onSubmit={onSubmit}>
      <Input
        label={t('books.dialog.fields.titleLabel')}
        value={title}
        onChange={(event) => onTitleChange(event.target.value)}
        placeholder={t('books.dialog.fields.titlePlaceholder')}
        required
        compact
        autoFocus
      />
      <div className={styles.descriptionField}>
        <label className={styles.descriptionLabel} htmlFor="book-summary">
          {t('books.dialog.fields.summaryLabel')}
        </label>
        <textarea
          id="book-summary"
          className={styles.descriptionTextarea}
          value={summary}
          onChange={(event) => onSummaryChange(event.target.value)}
          placeholder={t('books.dialog.fields.summaryPlaceholder')}
          rows={3}
        />
        <span className={styles.helperText}>{t('books.dialog.fields.summaryHelper')}</span>
      </div>

      <CoverIconSelector value={coverIconId} onChange={onCoverIconChange} />

      <TagMultiSelect
        label={t('books.dialog.fields.tagsLabel')}
        limitNote={t('books.dialog.fields.tagsLimitNote', { max: MAX_TAGS })}
        maxTags={MAX_TAGS}
        helperText={t('books.dialog.fields.tagsHelper')}
        canAddMore={canAddMoreTags}
        selections={tagSelections}
        inputValue={tagInput}
        disabled={isSaving}
        statusText={suggestionsLoading ? t('books.dialog.tags.loading') : undefined}
        suggestions={suggestions}
        suggestionsLabel={suggestionLabel}
        suggestionsLoading={suggestionsLoading}
        suggestionEmptyMessage={suggestionEmptyMessage}
        onInputChange={onTagInputChange}
        onInputKeyDown={onTagInputKeyDown}
        onRemoveTag={onRemoveTag}
        onSelectSuggestion={onSelectSuggestion}
      />

      {formError && <span className={styles.errorText}>{formError}</span>}
    </form>
  );
};
