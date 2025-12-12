'use client';

import React from 'react';
import type { BookCoverIconId } from '@/entities/book';
import { BookCoverIconPicker } from '../BookCoverIconPicker';
import styles from '../BookEditDialog.module.css';
import { useI18n } from '@/i18n/useI18n';

interface CoverIconSelectorProps {
  value: BookCoverIconId | null;
  onChange: (next: BookCoverIconId | null) => void;
}

export const CoverIconSelector: React.FC<CoverIconSelectorProps> = ({ value, onChange }) => {
  const { t } = useI18n();
  return (
    <div className={styles.coverIconField}>
      <div className={styles.labelRow}>
        <span>{t('books.dialog.fields.coverIconLabel')}</span>
        <span className={styles.limitNote}>{t('books.dialog.fields.coverIconDescription')}</span>
      </div>
      <p className={styles.helperText}>{t('books.dialog.fields.coverIconHelper')}</p>
      <BookCoverIconPicker value={value} onChange={onChange} />
    </div>
  );
};
