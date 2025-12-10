'use client';

import React from 'react';
import { BookDto, BookMaturity } from '@/entities/book';
import styles from './BookPreviewCard.module.css';
import { BookDisplayCabinet } from './BookDisplayCabinet';

interface BookPreviewCardProps {
  book: BookDto;
  onSelect?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onConfigureCover?: (id: string) => void;
  tagDescriptionsMap?: Record<string, string>;
}

/**
 * BookPreviewCard
 * 用于横向滚动列表显示书籍预览卡片
 * 特点：
 * - 200×280px 卡片尺寸
 * - 彩色封面（根据书名哈希生成）
 * - 书名 + 描述摘要
 * - 悬停显示操作菜单
 */
export const BookPreviewCard = React.forwardRef<HTMLDivElement, BookPreviewCardProps>(
  ({ book, onSelect, onEdit, onDelete, onConfigureCover, tagDescriptionsMap }, ref) => {
    const [showMenu, setShowMenu] = React.useState(false);

    const maturity = (book.maturity || 'seed') as BookMaturity;
    const maturityClass = styles[`maturity${maturity.charAt(0).toUpperCase() + maturity.slice(1)}`] || '';
    const maturityLabels: Record<BookMaturity, string> = {
      seed: 'Seed · 草创',
      growing: 'Growing · 成长',
      stable: 'Stable · 稳定',
      legacy: 'Legacy · 归档',
    };
    const allowMutate = maturity !== 'legacy';
    const canConfigureCover = !!onConfigureCover && maturity === 'stable';

    const statusColors: Record<string, string> = {
      DRAFT: '#6B7280',
      PUBLISHED: '#16A34A',
      ARCHIVED: '#78350F',
      DELETED: '#DC2626',
    };
    const statusColor = statusColors[book.status] || '#6B7280';

    return (
      <div
        ref={ref}
        className={`${styles.cardWrapper} ${styles[`wrapper${maturity.charAt(0).toUpperCase() + maturity.slice(1)}`] || ''}`}
        onMouseEnter={() => setShowMenu(true)}
        onMouseLeave={() => setShowMenu(false)}
        data-maturity={maturity}
      >
        <div
          className={`${styles.card} ${maturityClass}`}
          onClick={() => {
            if (onSelect) onSelect(book.id);
          }}
          data-maturity={maturity}
        >
          <div className={styles.displayArea}>
            <BookDisplayCabinet
              book={book}
              maturity={maturity}
              statusColor={statusColor}
              tagDescriptionsMap={tagDescriptionsMap}
            />
          </div>

          {/* 内容 */}
          <div className={styles.content}>
            <div className={styles.maturityTag} data-maturity={maturity}>
              {maturityLabels[maturity]}
            </div>
            <h3 className={styles.title}>{book.title}</h3>
            {book.summary && (
              <p className={styles.summary}>{book.summary}</p>
            )}
            <div className={styles.meta}>
              <span className={styles.blocks} title="内容块数">
                📄 {book.block_count || 0}
              </span>
              {book.due_at && (
                <span className={styles.due} title="到期时间">
                  ⏰ {new Date(book.due_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          {/* 悬停菜单 */}
          {showMenu && (
            <div className={styles.menu}>
              {onSelect && (
                <button
                  className={styles.menuBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelect(book.id);
                  }}
                  title="查看详情"
                >
                  👁️
                </button>
              )}
              {onEdit && allowMutate && (
                <button
                  className={styles.menuBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(book.id);
                  }}
                  title="编辑"
                >
                  ✏️
                </button>
              )}
              {onDelete && allowMutate && (
                <button
                  className={styles.menuBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(book.id);
                  }}
                  title="删除"
                >
                  🗑️
                </button>
              )}
              {onConfigureCover && (
                canConfigureCover ? (
                  <button
                    className={styles.menuBtn}
                    onClick={(e) => {
                      e.stopPropagation();
                      onConfigureCover(book.id);
                    }}
                    title="配置封面"
                  >
                    🖼️
                  </button>
                ) : (
                  <button
                    className={`${styles.menuBtn} ${styles.menuBtnDisabled}`}
                    onClick={(e) => e.stopPropagation()}
                    title="仅稳定书籍可配置封面"
                    disabled
                  >
                    🖼️
                  </button>
                )
              )}
              {!allowMutate && (
                <span className={styles.readonlyHint}>只读模式</span>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }
);

BookPreviewCard.displayName = 'BookPreviewCard';
