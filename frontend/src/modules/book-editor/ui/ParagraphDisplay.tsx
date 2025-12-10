'use client';

import React from 'react';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface ParagraphDisplayProps {
  blockId: string;
  text: string;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const ParagraphDisplay: React.FC<ParagraphDisplayProps> = ({ text, onStartEdit }) => {
  return (
    <div
      className={`${styles.textBlockShell} ${styles.textBlockContent}`}
      role="textbox"
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          onStartEdit({ source: 'key', key: event.key, shiftKey: event.shiftKey });
        }
      }}
    >
      {text ? text : <span className={styles.placeholder}>写点什么…</span>}
    </div>
  );
};
