'use client';

import React from 'react';
import type { HeadingBlockContent } from '@/entities/block';
import { ParagraphEditor, ParagraphEditorProps } from './ParagraphEditor';

interface HeadingEditorProps extends Omit<ParagraphEditorProps, 'value' | 'variant' | 'onChange'> {
  blockId: string;
  content: HeadingBlockContent;
  onChange: (next: HeadingBlockContent) => void;
}

export const HeadingEditor: React.FC<HeadingEditorProps> = ({ content, onChange, ...rest }) => {
  const variant = (`heading-${content.level}` as ParagraphEditorProps['variant']);
  return (
    <ParagraphEditor
      value={content.text}
      variant={variant}
      {...rest}
      onChange={(value) => onChange({ ...content, text: value })}
    />
  );
};
