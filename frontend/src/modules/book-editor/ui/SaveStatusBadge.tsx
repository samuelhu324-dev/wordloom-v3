'use client';

import React from 'react';
import styles from './bookEditor.module.css';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';

type SaveState = 'idle' | 'saving' | 'saved' | 'error';

interface SaveStatusBadgeProps {
  state: SaveState;
}

const LABEL_KEYS: Record<SaveState, MessageKey | null> = {
  idle: null,
  saving: 'books.blocks.editor.save.saving',
  saved: null,
  error: 'books.blocks.editor.save.error',
};

export const SaveStatusBadge: React.FC<SaveStatusBadgeProps> = ({ state }) => {
  const { t } = useI18n();
  const labelKey = LABEL_KEYS[state];
  const label = labelKey ? t(labelKey) : null;
  if (!label) return null;
  return <span className={styles.statusBadge}>{label}</span>;
};

export type { SaveState };
