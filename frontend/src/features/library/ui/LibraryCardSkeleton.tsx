import React from 'react';
import styles from './LibraryCardSkeleton.module.css';

interface LibraryCardSkeletonProps {
  variant?: 'grid' | 'list';
}

export const LibraryCardSkeleton: React.FC<LibraryCardSkeletonProps> = ({ variant = 'grid' }) => {
  if (variant === 'list') {
    return (
      <div className={styles.listRow} aria-hidden>
        <div className={`${styles.listCover} ${styles.shimmer}`} />
        <div className={styles.listTitle}>
          <div className={`${styles.line} ${styles.lineWide} ${styles.shimmer}`} />
          <div className={`${styles.pill} ${styles.shimmer}`} />
        </div>
        <div className={styles.listDescription}>
          <div className={`${styles.line} ${styles.lineWide} ${styles.shimmer}`} />
          <div className={`${styles.line} ${styles.lineMedium} ${styles.shimmer}`} />
        </div>
        <div className={styles.listMetrics}>
          <div className={`${styles.listMetricDot} ${styles.shimmer}`} />
          <div className={`${styles.listMetricDot} ${styles.shimmer}`} />
          <div className={`${styles.listMetricDot} ${styles.shimmer}`} />
          <div className={`${styles.listMetricDot} ${styles.shimmer}`} />
        </div>
        <div className={styles.listDates}>
          <div className={`${styles.line} ${styles.lineMedium} ${styles.shimmer}`} />
          <div className={`${styles.line} ${styles.lineShort} ${styles.shimmer}`} />
        </div>
      </div>
    );
  }

  return (
    <div className={styles.card} aria-hidden>
      <div className={`${styles.cover} ${styles.shimmer}`} />
      <div className={styles.body}>
        <div className={`${styles.line} ${styles.lineTall} ${styles.lineWide} ${styles.shimmer}`} />
        <div className={`${styles.line} ${styles.lineMedium} ${styles.shimmer}`} />
        <div className={`${styles.tagRow}`}>
          <div className={`${styles.tag} ${styles.shimmer}`} />
          <div className={`${styles.tag} ${styles.shimmer}`} />
          <div className={`${styles.tag} ${styles.shimmer}`} />
        </div>
        <div className={styles.metrics}>
          <div className={`${styles.metricDot} ${styles.shimmer}`} />
          <div className={`${styles.metricDot} ${styles.shimmer}`} />
          <div className={`${styles.metricDot} ${styles.shimmer}`} />
          <div className={`${styles.metricDot} ${styles.shimmer}`} />
        </div>
        <div className={`${styles.line} ${styles.lineShort} ${styles.shimmer}`} />
      </div>
    </div>
  );
};
