'use client';

import React from 'react';
import { useBlockCommands } from '../model/blockCommands';
import styles from './bookEditor.module.css';
import { useI18n } from '@/i18n/useI18n';

interface InlineCreateBarProps {
  lastFractionalIndex?: string;
  onBlockCreated?: (blockId: string) => void;
}

export const InlineCreateBar: React.FC<InlineCreateBarProps> = ({ lastFractionalIndex, onBlockCreated }) => {
  const { createBlock } = useBlockCommands();
  const [isCreating, setIsCreating] = React.useState(false);
  const { t } = useI18n();

  const handleClick = async () => {
    if (isCreating) return;
    setIsCreating(true);
    try {
      await createBlock({
        position: {
          before: lastFractionalIndex,
        },
        selectionEdge: 'start',
        onCreated: (id) => onBlockCreated?.(id),
      });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div
      className={styles.inlineBar}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          handleClick();
        }
      }}
    >
      {isCreating ? t('books.blocks.editor.inlineCreate.loading') : t('books.blocks.editor.inlineCreate.placeholder')}
    </div>
  );
};
