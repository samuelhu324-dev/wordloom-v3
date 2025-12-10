'use client';

import React from 'react';
import type { CustomBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface CustomBlockDisplayProps {
  content: CustomBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const CustomBlockDisplay: React.FC<CustomBlockDisplayProps> = ({ content, onStartEdit }) => {
  return (
    <div className={styles.customBlock}>
      <header>
        <span>Legacy Custom Block</span>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onStartEdit({ source: 'click' });
          }}
        >
          编辑 JSON
        </button>
      </header>
      <pre>{JSON.stringify(content ?? {}, null, 2)}</pre>
    </div>
  );
};

interface CustomBlockEditorProps {
  content: CustomBlockContent;
  onChange: (next: CustomBlockContent) => void;
  onExitEdit: () => void;
}

export const CustomBlockEditor: React.FC<CustomBlockEditorProps> = ({ content, onChange, onExitEdit }) => {
  const [draft, setDraft] = React.useState(() => JSON.stringify(content ?? {}, null, 2));
  React.useEffect(() => {
    setDraft(JSON.stringify(content ?? {}, null, 2));
  }, [content]);

  const handleSave = () => {
    try {
      const parsed = JSON.parse(draft || '{}');
      onChange(parsed);
      onExitEdit();
    } catch (error) {
      alert('JSON 无法解析，请检查格式');
    }
  };

  return (
    <div className={styles.customBlockEditor}>
      <textarea value={draft} onChange={(event) => setDraft(event.target.value)} />
      <div className={styles.formActions}>
        <button type="button" className={styles.primaryButton} onClick={handleSave}>
          保存
        </button>
        <button type="button" className={styles.secondaryButton} onClick={onExitEdit}>
          取消
        </button>
      </div>
    </div>
  );
};
