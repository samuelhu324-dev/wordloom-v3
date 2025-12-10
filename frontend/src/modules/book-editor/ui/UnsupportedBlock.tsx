'use client';

import React from 'react';

interface UnsupportedBlockProps {
  kind: string;
}

export const UnsupportedBlock: React.FC<UnsupportedBlockProps> = ({ kind }) => {
  return (
    <div>
      <p>暂不支持的块类型：{kind}</p>
    </div>
  );
};
