import React from 'react';
import { MediaDto } from '@/entities/media';
import { Card, Button } from '@/shared/ui';
import styles from './MediaCard.module.css';

interface MediaCardProps {
  media: MediaDto;
  onDelete?: (id: string) => void;
  onRestore?: (id: string) => void;
}

export const MediaCard = React.forwardRef<HTMLDivElement, MediaCardProps>(
  ({ media, onDelete, onRestore }, ref) => {
    return (
      <Card ref={ref} className={styles.card}>
        <div className={styles.preview}>
          {media.mime_type.startsWith('image/') ? (
            <img src={media.path} alt={media.path} className={styles.image} />
          ) : (
            <div className={styles.filetype}>{media.media_type}</div>
          )}
        </div>
        <div className={styles.content}>
          <h4>{media.path.split('/').pop()}</h4>
          <p className={styles.meta}>{(media.size_bytes / 1024).toFixed(2)} KB</p>
          {media.trashed_at && <span className={styles.deleted}>已删除</span>}
        </div>
        <div className={styles.actions}>
          {media.trashed_at && onRestore && (
            <Button variant="secondary" size="sm" onClick={() => onRestore(media.id)}>
              恢复
            </Button>
          )}
          {onDelete && (
            <Button variant="danger" size="sm" onClick={() => onDelete(media.id)}>
              删除
            </Button>
          )}
        </div>
      </Card>
    );
  }
);

MediaCard.displayName = 'MediaCard';
