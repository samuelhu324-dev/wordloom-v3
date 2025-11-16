import React from 'react';
import { BlockDto } from '@/entities/block';
import { Spinner } from '@/shared/ui';
import { BlockCard } from './BlockCard';
import styles from './BlockList.module.css';

interface BlockListProps {
  blocks: BlockDto[];
  isLoading?: boolean;
  onSelectBlock?: (id: string) => void;
  onDeleteBlock?: (id: string) => void;
}

export const BlockList = React.forwardRef<HTMLDivElement, BlockListProps>(
  ({ blocks, isLoading, onSelectBlock, onDeleteBlock }, ref) => {
    if (isLoading) {
      return (
        <div className={styles.container} ref={ref}>
          <Spinner />
        </div>
      );
    }

    if (blocks.length === 0) {
      return (
        <div className={styles.empty} ref={ref}>
          <p>No blocks yet. Create one to get started!</p>
        </div>
      );
    }

    return (
      <div className={styles.list} ref={ref}>
        {blocks.map((block) => (
          <BlockCard
            key={block.id}
            block={block}
            onSelect={onSelectBlock}
            onDelete={onDeleteBlock}
          />
        ))}
      </div>
    );
  }
);

BlockList.displayName = 'BlockList';
