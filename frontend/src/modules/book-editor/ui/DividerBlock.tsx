'use client';

import React from 'react';
import type { DividerBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';

interface DividerDisplayProps {
  content: DividerBlockContent;
}

export const DividerDisplay: React.FC<DividerDisplayProps> = ({ content }) => {
  return (
    <div className={styles.dividerBlock} data-variant={content.style || 'solid'}>
      <span />
    </div>
  );
};

interface DividerEditorProps {
  content: DividerBlockContent;
  onChange: (next: DividerBlockContent) => void;
  onExitEdit: () => void;
}

export const DividerEditor: React.FC<DividerEditorProps> = ({ content, onChange, onExitEdit }) => {
  return (
    <div className={styles.dividerEditor}>
      <label>
        <input
          type="radio"
          checked={!content.style || content.style === 'solid'}
          onChange={() => onChange({ style: 'solid' })}
        />
        实线
      </label>
      <label>
        <input
          type="radio"
          checked={content.style === 'dashed'}
          onChange={() => onChange({ style: 'dashed' })}
        />
        虚线
      </label>
      <div className={styles.formActions}>
        <button type="button" className={styles.primaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
