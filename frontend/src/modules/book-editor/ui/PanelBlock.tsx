'use client';

import React from 'react';
import type { PanelBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface PanelDisplayProps {
  content: PanelBlockContent;
  onStartEdit?: (request?: BlockEditorStartEditRequest) => void;
}

export const PanelDisplay: React.FC<PanelDisplayProps> = ({ content, onStartEdit }) => {
  const { title, body, imageUrl, layout = 'one-column' } = content;
  return (
    <button
      type="button"
      className={styles.panelBlock}
      data-layout={layout}
      onClick={() => onStartEdit?.({ source: 'click' })}
    >
      {imageUrl ? (
        <div className={styles.panelImage} style={{ backgroundImage: `url(${imageUrl})` }} />
      ) : (
        <div className={styles.panelImagePlaceholder}>添加图片</div>
      )}
      <div className={styles.panelContentArea}>
        <p className={styles.panelTitle}>{title?.trim() ? title : '未命名窗格'}</p>
        <p className={styles.panelBody}>{body?.trim() ? body : '点击编辑窗格内容…'}</p>
      </div>
    </button>
  );
};

interface PanelEditorProps {
  content: PanelBlockContent;
  onChange: (next: PanelBlockContent) => void;
  onExitEdit: () => void;
}

export const PanelEditor: React.FC<PanelEditorProps> = ({ content, onChange, onExitEdit }) => {
  const handleFieldChange = (field: keyof PanelBlockContent, value: string) => {
    onChange({ ...content, [field]: value });
  };

  return (
    <div className={styles.panelEditor}>
      <div className={styles.panelEditorRow}>
        <label className={styles.panelEditorLabel}>
          布局
          <select
            className={styles.panelEditorSelect}
            value={content.layout ?? 'one-column'}
            onChange={(event) => handleFieldChange('layout', event.target.value)}
          >
            <option value="one-column">单列</option>
            <option value="two-column">双列</option>
          </select>
        </label>
        <label className={styles.panelEditorLabel}>
          图片 URL
          <input
            type="url"
            className={styles.panelEditorInput}
            placeholder="https://example.com/cover.jpg"
            value={content.imageUrl ?? ''}
            onChange={(event) => handleFieldChange('imageUrl', event.target.value)}
          />
        </label>
      </div>
      <label className={styles.panelEditorLabel}>
        标题
        <input
          type="text"
          className={styles.panelEditorInput}
          placeholder="窗格标题"
          value={content.title ?? ''}
          onChange={(event) => handleFieldChange('title', event.target.value)}
        />
      </label>
      <label className={styles.panelEditorLabel}>
        正文
        <textarea
          className={styles.panelEditorTextarea}
          placeholder="写点说明文案..."
          value={content.body ?? ''}
          onChange={(event) => handleFieldChange('body', event.target.value)}
        />
      </label>
      <div className={styles.formActions}>
        <button type="button" className={styles.secondaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
