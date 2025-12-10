'use client';

import React, { useEffect, useRef } from 'react';
import { BookDto } from '@/entities/book';
import { Spinner } from '@/shared/ui';
import { BookPreviewCard } from './BookPreviewCard';
import styles from './BookPreviewList.module.css';

interface BookPreviewListProps {
  books: BookDto[];
  isLoading?: boolean;
  onSelectBook?: (id: string) => void;
  onEditBook?: (id: string) => void;
  onDeleteBook?: (id: string) => void;
  onConfigureCover?: (id: string) => void;
  layout?: 'horizontal' | 'grid';
  hasMore?: boolean;
  onLoadMore?: () => void;
  useIntersection?: boolean; // 默认 true：水平 & 网格均支持
  tagDescriptionsMap?: Record<string, string>;
}

/**
 * BookPreviewList
 * 横向滚动的书籍预览卡片列表
 * 特点：
 * - CSS 原生横向滚动
 * - 响应式卡片（200px 宽度）
 * - 支持空状态提示
 */
export const BookPreviewList = React.forwardRef<HTMLDivElement, BookPreviewListProps>(
  ({ books, isLoading, onSelectBook, onEditBook, onDeleteBook, onConfigureCover, layout = 'horizontal', hasMore, onLoadMore, useIntersection = true, tagDescriptionsMap }, ref) => {
    const sentinelRef = useRef<HTMLDivElement | null>(null);

    // 交叉观察：自动加载更多
    useEffect(() => {
      if (!useIntersection || !hasMore) return;
      const el = sentinelRef.current;
      if (!el) return;
      const observer = new IntersectionObserver((entries) => {
        const first = entries[0];
        if (first.isIntersecting) {
          onLoadMore && onLoadMore();
        }
      }, { rootMargin: '120px' });
      observer.observe(el);
      return () => observer.disconnect();
    }, [hasMore, onLoadMore, useIntersection]);
    if (isLoading) {
      return (
        <div className={styles.container} ref={ref}>
          <div className={styles.loadingState}>
            <Spinner />
            <p>加载中...</p>
          </div>
        </div>
      );
    }

    if (!books || books.length === 0) {
      return (
        <div className={styles.container} ref={ref}>
          <div className={styles.emptyState}>
            <p>📚 暂无书籍</p>
            <span>点击“添加书籍”开始创建</span>
          </div>
        </div>
      );
    }

    const wrapperClass = layout === 'grid' ? styles.gridWrapper : styles.scrollWrapper;

    return (
      <div className={styles.container} ref={ref}>
        <div className={wrapperClass}>
          {books.map((book) => (
            <BookPreviewCard
              key={book.id}
              book={book}
              onSelect={onSelectBook}
              onEdit={onEditBook}
              onDelete={onDeleteBook}
              onConfigureCover={onConfigureCover}
              tagDescriptionsMap={tagDescriptionsMap}
            />
          ))}
          {hasMore && !isLoading && !useIntersection && (
            <div className={styles.loadMoreWrapper}>
              <button className={styles.loadMoreBtn} onClick={onLoadMore}>加载更多...</button>
            </div>
          )}
        </div>
        {hasMore && useIntersection && (
          <div ref={sentinelRef} className={styles.sentinel} aria-label="加载更多标记" />
        )}
      </div>
    );
  }
);

BookPreviewList.displayName = 'BookPreviewList';
