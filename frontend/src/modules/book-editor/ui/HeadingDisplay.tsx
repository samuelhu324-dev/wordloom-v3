'use client';

import React from 'react';
import type { HeadingBlockContent } from '@/entities/block';
import styles from './bookEditor.module.css';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';

interface HeadingDisplayProps {
  blockId: string;
  content: HeadingBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

const headingTagMap: Record<HeadingBlockContent['level'], keyof JSX.IntrinsicElements> = {
  1: 'h1',
  2: 'h2',
  3: 'h3',
};

export const HeadingDisplay: React.FC<HeadingDisplayProps> = ({ content, onStartEdit }) => {
  const Tag = headingTagMap[content.level] ?? 'h2';
  return (
    <Tag
      className={styles.blockDisplay}
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
    >
      {content.text || <span className={styles.placeholder}>标题</span>}
    </Tag>
  );
};
