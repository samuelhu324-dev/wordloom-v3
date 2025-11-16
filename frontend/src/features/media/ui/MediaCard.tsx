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
          {media.type.startsWith('image/') ? (
            <img src={media.url} alt={media.filename} className={styles.image} />
          ) : (
            <div className={styles.filetype}>{media.type}</div>
          )}
        </div>
        <div className={styles.content}>
          <h4>{media.filename}</h4>
          <p className={styles.meta}>{(media.size / 1024).toFixed(2)} KB</p>
          {media.deleted_at && <span className={styles.deleted}>Deleted</span>}
        </div>
        <div className={styles.actions}>
          {media.deleted_at && onRestore && (
            <Button variant="secondary" size="sm" onClick={() => onRestore(media.id)}>
              Restore
            </Button>
          )}
          {onDelete && (
            <Button variant="danger" size="sm" onClick={() => onDelete(media.id)}>
              Delete
            </Button>
          )}
        </div>
      </Card>
    );
  }
);

MediaCard.displayName = 'MediaCard';
