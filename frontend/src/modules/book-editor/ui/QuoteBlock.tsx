'use client';

import React from 'react';
import type { QuoteBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface QuoteDisplayProps {
  content: QuoteBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const QuoteDisplay: React.FC<QuoteDisplayProps> = ({ content, onStartEdit }) => {
  return (
    <figure
      className={styles.quoteBlock}
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onStartEdit({ source: 'key', key: event.key, shiftKey: event.shiftKey });
        }
      }}
    >
      <blockquote>
        <p>{content.text || '引用内容'}</p>
      </blockquote>
      {content.source && <figcaption>— {content.source}</figcaption>}
    </figure>
  );
};

interface QuoteEditorProps {
  content: QuoteBlockContent;
  onChange: (next: QuoteBlockContent) => void;
  onExitEdit: () => void;
}

export const QuoteEditor: React.FC<QuoteEditorProps> = ({ content, onChange, onExitEdit }) => {
  return (
    <div className={styles.quoteEditor}>
      <textarea
        className={styles.quoteTextarea}
        value={content.text ?? ''}
        placeholder="引用内容"
        onChange={(event) => onChange({ ...content, text: event.target.value })}
      />
      <input
        type="text"
        className={styles.quoteSourceInput}
        value={content.source ?? ''}
        placeholder="来源（可选）"
        onChange={(event) => onChange({ ...content, source: event.target.value })}
      />
      <div className={styles.formActions}>
        <button type="button" className={styles.primaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
