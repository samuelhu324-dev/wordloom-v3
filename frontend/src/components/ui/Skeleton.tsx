/**
 * Skeleton Component
 * Loading placeholder for content
 */

import React from 'react';
import '@/styles/skeleton.css';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  count?: number;
  height?: string;
  width?: string;
}

export function Skeleton({
  count = 1,
  height = '1rem',
  width = '100%',
  className = '',
  ...props
}: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`skeleton ${className}`}
          style={{ height, width }}
          {...props}
        />
      ))}
    </>
  );
}
