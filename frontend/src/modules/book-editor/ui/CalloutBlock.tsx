'use client';

import React from 'react';
import type { CalloutBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

const VARIANTS: Array<NonNullable<CalloutBlockContent['variant']>> = ['info', 'warning', 'danger', 'success'];

interface CalloutDisplayProps {
  content: CalloutBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const CalloutDisplay: React.FC<CalloutDisplayProps> = ({ content, onStartEdit }) => {
  const variant = content.variant && VARIANTS.includes(content.variant) ? content.variant : 'info';
  return (
    <button
      type="button"
      className={`${styles.callout} ${styles[`callout-${variant}`] ?? ''}`}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
    >
      <span className={styles.calloutLabel}>{variant.toUpperCase()}</span>
      <p>{content.text || '暂无内容'}</p>
    </button>
  );
};

interface CalloutEditorProps {
  content: CalloutBlockContent;
  onChange: (next: CalloutBlockContent) => void;
  onExitEdit: () => void;
}

export const CalloutEditor: React.FC<CalloutEditorProps> = ({ content, onChange, onExitEdit }) => {
  const variant = content.variant && VARIANTS.includes(content.variant) ? content.variant : 'info';
  return (
    <div className={styles.calloutEditor}>
      <div className={styles.calloutVariantList}>
        {VARIANTS.map((option) => (
          <button
            key={option}
            type="button"
            className={`${styles.secondaryButton} ${variant === option ? styles.calloutVariantActive : ''}`}
            onClick={() => onChange({ ...content, variant: option })}
          >
            {option.toUpperCase()}
          </button>
        ))}
      </div>
      <textarea
        className={styles.calloutTextarea}
        value={content.text ?? ''}
        placeholder="需要强调的内容"
        onChange={(event) => onChange({ ...content, text: event.target.value })}
      />
      <div className={styles.formActions}>
        <button type="button" className={styles.primaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
