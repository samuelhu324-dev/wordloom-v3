'use client';

import React from 'react';
import { BookshelfDto } from '@/entities/bookshelf';
import styles from './BookshelfPreviewCard.module.css';

interface BookshelfPreviewCardProps {
  bookshelf: BookshelfDto;
  bookCount?: number;
  onClick?: () => void;
  coverImage?: string;
}

/**
 * BookshelfPreviewCard
 * 用于 Library 详情页显示书橱预览
 * 特点：
 * - 大插图区域（aspect-ratio 3:4）
 * - 悬停时显示覆盖层
 * - 书橱名称 + 描述 + 书籍数量徽章
 */
export const BookshelfPreviewCard = React.forwardRef<HTMLDivElement, BookshelfPreviewCardProps>(
  ({ bookshelf, bookCount = 0, onClick, coverImage }, ref) => {
    // Placeholder 颜色（基于 bookshelf type）
    const placeholderGradient = bookshelf.type === 'BASEMENT'
      ? 'linear-gradient(135deg, #e74c3c, #c0392b)'
      : 'linear-gradient(135deg, #3498db, #2980b9)';

    return (
      <div
        ref={ref}
        className={styles.card}
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyPress={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onClick?.();
          }
        }}
      >
        {/* Cover Image Area */}
        <div className={styles.cover} style={{ background: coverImage ? 'none' : placeholderGradient }}>
          {coverImage ? (
            <img src={coverImage} alt={bookshelf.name} />
          ) : (
            <div className={styles.placeholder}>
              <span className={styles.icon}>📚</span>
            </div>
          )}
          <div className={styles.overlay}>
            <span className={styles.overlayText}>查看详情</span>
          </div>
        </div>

        {/* Content Area */}
        <div className={styles.content}>
          <h3 className={styles.title}>{bookshelf.name}</h3>
          <p className={styles.description}>{bookshelf.description || '无描述'}</p>
          <div className={styles.badge}>
            📖 {bookCount} 本书
          </div>
        </div>
      </div>
    );
  }
);

BookshelfPreviewCard.displayName = 'BookshelfPreviewCard';
