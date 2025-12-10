import React from 'react';
import { TagDto } from '@/entities/tag';
import { Button } from '@/shared/ui';
import styles from './TagBadge.module.css';

interface TagBadgeProps {
  tag: TagDto;
  onRemove?: (id: string) => void;
}

export const TagBadge = React.forwardRef<HTMLDivElement, TagBadgeProps>(
  ({ tag, onRemove }, ref) => {
    return (
      <div ref={ref} className={styles.badge}>
        <span>{tag.name}</span>
        {onRemove && (
          <Button variant="secondary" size="sm" onClick={() => onRemove(tag.id)}>
            ×
          </Button>
        )}
      </div>
    );
  }
);

TagBadge.displayName = 'TagBadge';
