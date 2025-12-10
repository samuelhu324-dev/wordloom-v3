'use client';

import React from 'react';
import styles from './bookEditor.module.css';
import { useI18n } from '@/i18n/useI18n';

interface BlockToolbarProps {
  onOpenMenu: (anchorRect: DOMRect | null) => void;
  disabled?: boolean;
}

export const BlockToolbar: React.FC<BlockToolbarProps> = ({ onOpenMenu, disabled }) => {
  const { t } = useI18n();
  return (
    <div className={styles.toolbar} data-block-toolbar="true">
      <button
        type="button"
        className={styles.toolbarButton}
        onClick={(event) => {
          event.stopPropagation();
          const rect = event.currentTarget.getBoundingClientRect();
          onOpenMenu(rect ?? null);
        }}
        disabled={disabled}
        aria-label={t('books.blocks.editor.toolbar.addBlock.aria')}
      >
        ...
      </button>
    </div>
  );
};
