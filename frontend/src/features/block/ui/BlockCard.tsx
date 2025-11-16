import React from 'react';
import { BlockDto } from '@/entities/block';
import { Card, Button } from '@/shared/ui';
import styles from './BlockCard.module.css';

interface BlockCardProps {
  block: BlockDto;
  onSelect?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const BlockCard = React.forwardRef<HTMLDivElement, BlockCardProps>(
  ({ block, onSelect, onDelete }, ref) => {
    return (
      <Card ref={ref} className={styles.card}>
        <div className={styles.header}>
          <span className={styles.type}>{block.type}</span>
          {onDelete && (
            <Button variant="ghost" size="sm" onClick={() => onDelete(block.id)}>
              ×
            </Button>
          )}
        </div>
        <p className={styles.content}>{block.content?.substring(0, 100)}...</p>
        {onSelect && (
          <Button variant="secondary" size="sm" onClick={() => onSelect(block.id)}>
            Edit
          </Button>
        )}
      </Card>
    );
  }
);

BlockCard.displayName = 'BlockCard';
