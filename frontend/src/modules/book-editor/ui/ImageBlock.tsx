'use client';

import React from 'react';
import type { ImageBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface ImageBlockDisplayProps {
  content: ImageBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const ImageBlockDisplay: React.FC<ImageBlockDisplayProps> = ({ content, onStartEdit }) => {
  const hasImage = Boolean(content?.url);
  return (
    <div className={styles.imageBlock}>
      {hasImage ? (
        <button
          type="button"
          className={styles.imageButton}
          onClick={(event) => {
            event.stopPropagation();
            onStartEdit({ source: 'click' });
          }}
        >
          <img src={content.url} alt={content.caption || '图片块'} />
        </button>
      ) : (
        <button
          type="button"
          className={styles.imagePlaceholder}
          onClick={(event) => {
            event.stopPropagation();
            onStartEdit({ source: 'click' });
          }}
        >
          上传图片
        </button>
      )}
      {content.caption && <p className={styles.imageCaption}>{content.caption}</p>}
    </div>
  );
};

interface ImageBlockEditorProps {
  content: ImageBlockContent;
  onChange: (next: ImageBlockContent) => void;
  onExitEdit: () => void;
}

export const ImageBlockEditor: React.FC<ImageBlockEditorProps> = ({ content, onChange, onExitEdit }) => {
  return (
    <div className={styles.imageEditor}>
      <label className={styles.imageField}>
        图片 URL
        <input
          type="url"
          value={content.url ?? ''}
          placeholder="https://example.com/pic.jpg"
          onChange={(event) => onChange({ ...content, url: event.target.value })}
        />
      </label>
      <label className={styles.imageField}>
        Caption
        <input
          type="text"
          value={content.caption ?? ''}
          placeholder="图片说明"
          onChange={(event) => onChange({ ...content, caption: event.target.value })}
        />
      </label>
      <div className={styles.formActions}>
        <button type="button" className={styles.primaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
