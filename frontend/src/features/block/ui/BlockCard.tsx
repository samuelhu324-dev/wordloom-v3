import React from 'react';
import { BlockDto, getParagraphText } from '@/entities/block';
import { Card, Button } from '@/shared/ui';
import styles from './BlockCard.module.css';

interface BlockCardProps {
  block: BlockDto;
  onSelect?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const extractPreviewText = (block: BlockDto): string => {
  if (block.kind === 'paragraph') {
    return getParagraphText(block);
  }
  if (typeof block.content === 'string') {
    return block.content;
  }
  if (block.content && typeof block.content === 'object' && 'text' in block.content) {
    const textValue = (block.content as { text?: unknown }).text;
    return typeof textValue === 'string' ? textValue : String(textValue ?? '');
  }
  return '';
};

export const BlockCard = React.forwardRef<HTMLDivElement, BlockCardProps>(
  ({ block, onSelect, onDelete }, ref) => {
    const preview = extractPreviewText(block);
    const previewSnippet = preview ? `${preview.slice(0, 100)}${preview.length > 100 ? '...' : ''}` : '写点什么...';
    return (
      <Card ref={ref} className={styles.card}>
        <div className={styles.header}>
          <span className={styles.type}>{block.kind || block.type}</span>
          {onDelete && (
            <Button variant="secondary" size="sm" onClick={() => onDelete(block.id)}>
              ×
            </Button>
          )}
        </div>
        <p className={styles.content}>{previewSnippet}</p>
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
