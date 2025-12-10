import React from 'react';
import type { BookCoverIconId } from '@/entities/book';
import { BookCoverIconPicker } from '../BookCoverIconPicker';
import styles from '../BookEditDialog.module.css';

interface CoverIconSelectorProps {
  value: BookCoverIconId | null;
  onChange: (next: BookCoverIconId | null) => void;
}

export const CoverIconSelector: React.FC<CoverIconSelectorProps> = ({ value, onChange }) => (
  <div className={styles.coverIconField}>
    <div className={styles.labelRow}>
      <span>封面图标</span>
      <span className={styles.limitNote}>在展柜 / List 封面上展示 Lucide 图标</span>
    </div>
    <p className={styles.helperText}>未选择时按首字母+默认封面展示，可随时切换或清除。</p>
    <BookCoverIconPicker value={value} onChange={onChange} />
  </div>
);
