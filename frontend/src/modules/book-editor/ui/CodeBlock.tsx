'use client';

import React from 'react';
import type { CodeBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface CodeBlockDisplayProps {
  content: CodeBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const CodeBlockDisplay: React.FC<CodeBlockDisplayProps> = ({ content, onStartEdit }) => {
  return (
    <pre
      className={styles.codeBlock}
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
    >
      <code>{content.code || '```'}</code>
    </pre>
  );
};

interface CodeBlockEditorProps {
  content: CodeBlockContent;
  onChange: (next: CodeBlockContent) => void;
  onExitEdit: () => void;
}

export const CodeBlockEditor: React.FC<CodeBlockEditorProps> = ({ content, onChange, onExitEdit }) => {
  return (
    <div className={styles.codeEditor}>
      <label className={styles.imageField}>
        语言
        <input
          type="text"
          value={content.language ?? ''}
          placeholder="text"
          onChange={(event) => onChange({ ...content, language: event.target.value })}
        />
      </label>
      <textarea
        className={styles.codeTextarea}
        value={content.code ?? ''}
        placeholder="代码内容"
        onChange={(event) => onChange({ ...content, code: event.target.value })}
      />
      <div className={styles.formActions}>
        <button type="button" className={styles.primaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
