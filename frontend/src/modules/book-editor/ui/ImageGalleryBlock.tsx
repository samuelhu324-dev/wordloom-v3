'use client';

import React from 'react';
import type { ImageGalleryBlockContent, ImageGalleryItemContent } from '@/entities/block';
import { generateBlockScopedId } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface ImageGalleryDisplayProps {
  content: ImageGalleryBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const ImageGalleryDisplay: React.FC<ImageGalleryDisplayProps> = ({ content, onStartEdit }) => {
  const layout = content.layout === 'grid' ? 'grid' : 'strip';
  const items = Array.isArray(content?.items) ? content.items : [];
  return (
    <div
      className={`${styles.imageGallery} ${layout === 'grid' ? styles.imageGalleryGrid : styles.imageGalleryStrip}`}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
      role="button"
      tabIndex={0}
    >
      {items.length === 0 ? (
        <span className={styles.placeholder}>暂无图片，点击编辑添加</span>
      ) : (
        items.map((item) => (
          <figure key={item.id} className={styles.galleryItem}>
            {item.url ? <img src={item.url} alt={item.caption || '图片'} /> : <div className={styles.imagePlaceholder}>无图片</div>}
            {(item.indexLabel || item.caption) && (
              <figcaption>
                {item.indexLabel && <strong>{item.indexLabel}</strong>}
                {item.caption && <span>{item.caption}</span>}
              </figcaption>
            )}
          </figure>
        ))
      )}
    </div>
  );
};

interface ImageGalleryEditorProps {
  content: ImageGalleryBlockContent;
  onChange: (next: ImageGalleryBlockContent) => void;
  onExitEdit: () => void;
}

export const ImageGalleryEditor: React.FC<ImageGalleryEditorProps> = ({ content, onChange, onExitEdit }) => {
  const layout = content.layout === 'grid' ? 'grid' : 'strip';
  const items = Array.isArray(content?.items) ? content.items : [];

  const updateItem = (target: ImageGalleryItemContent, patch: Partial<ImageGalleryItemContent>) => {
    const nextItems = items.map((item) => (item.id === target.id ? { ...item, ...patch } : item));
    onChange({ ...content, items: nextItems });
  };

  const removeItem = (target: ImageGalleryItemContent) => {
    onChange({ ...content, items: items.filter((item) => item.id !== target.id) });
  };

  const addItem = () => {
    const nextItem: ImageGalleryItemContent = { id: generateBlockScopedId(), url: '', caption: '' };
    onChange({ ...content, items: [...items, nextItem] });
  };

  return (
    <div className={styles.galleryEditor}>
      <div className={styles.galleryLayoutOptions}>
        <button
          type="button"
          className={`${styles.secondaryButton} ${layout === 'strip' ? styles.galleryLayoutActive : ''}`}
          onClick={() => onChange({ ...content, layout: 'strip' })}
        >
          条形
        </button>
        <button
          type="button"
          className={`${styles.secondaryButton} ${layout === 'grid' ? styles.galleryLayoutActive : ''}`}
          onClick={() => onChange({ ...content, layout: 'grid' })}
        >
          网格
        </button>
        {layout === 'grid' && (
          <label className={styles.imageField}>
            每行数量
            <input
              type="number"
              min={2}
              max={6}
              value={content.maxPerRow ?? 3}
              onChange={(event) => onChange({ ...content, maxPerRow: Number(event.target.value) || 3 })}
            />
          </label>
        )}
      </div>
      {items.map((item, index) => (
        <div key={item.id ?? index} className={styles.galleryRow}>
          <input
            type="url"
            value={item.url ?? ''}
            placeholder="图片 URL"
            onChange={(event) => updateItem(item, { url: event.target.value })}
          />
          <input
            type="text"
            value={item.caption ?? ''}
            placeholder="说明"
            onChange={(event) => updateItem(item, { caption: event.target.value })}
          />
          <input
            type="text"
            value={item.indexLabel ?? ''}
            placeholder="序号"
            onChange={(event) => updateItem(item, { indexLabel: event.target.value })}
          />
          <button type="button" className={styles.dangerButton} onClick={() => removeItem(item)}>
            删除
          </button>
        </div>
      ))}
      <div className={styles.galleryActions}>
        <button type="button" className={styles.secondaryButton} onClick={addItem}>
          添加图片
        </button>
        <button type="button" className={styles.primaryButton} onClick={onExitEdit}>
          完成
        </button>
      </div>
    </div>
  );
};
