import React from 'react';
import { MediaDto } from '@/entities/media';
import { Spinner } from '@/shared/ui';
import { MediaCard } from './MediaCard';
import styles from './MediaList.module.css';

interface MediaListProps {
  media: MediaDto[];
  isLoading?: boolean;
  onDeleteMedia?: (id: string) => void;
  onRestoreMedia?: (id: string) => void;
}

export const MediaList = React.forwardRef<HTMLDivElement, MediaListProps>(
  ({ media, isLoading, onDeleteMedia, onRestoreMedia }, ref) => {
    if (isLoading) {
      return (
        <div className={styles.container} ref={ref}>
          <Spinner />
        </div>
      );
    }

    if (media.length === 0) {
      return (
        <div className={styles.empty} ref={ref}>
          <p>No media yet</p>
        </div>
      );
    }

    return (
      <div className={styles.grid} ref={ref}>
        {media.map((item) => (
          <MediaCard
            key={item.id}
            media={item}
            onDelete={onDeleteMedia}
            onRestore={onRestoreMedia}
          />
        ))}
      </div>
    );
  }
);

MediaList.displayName = 'MediaList';
