import React from 'react';
import { TagDto } from '@/entities/tag';
import { TagBadge } from './TagBadge';
import styles from './TagList.module.css';

interface TagListProps {
  tags: TagDto[];
  onRemoveTag?: (id: string) => void;
}

export const TagList = React.forwardRef<HTMLDivElement, TagListProps>(
  ({ tags, onRemoveTag }, ref) => {
    if (tags.length === 0) {
      return (
        <div className={styles.empty} ref={ref}>
          <p>No tags</p>
        </div>
      );
    }

    return (
      <div className={styles.container} ref={ref}>
        {tags.map((tag) => (
          <TagBadge key={tag.id} tag={tag} onRemove={onRemoveTag} />
        ))}
      </div>
    );
  }
);

TagList.displayName = 'TagList';
