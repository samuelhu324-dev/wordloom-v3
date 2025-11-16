'use client';

import React from 'react';
import { useLibraries } from '../model/hooks';
import { LibraryCard } from './LibraryCard';
import { Spinner } from '@/shared/ui';

export interface LibraryListProps {
  onSelectLibrary?: (id: string) => void;
  onEditLibrary?: (id: string) => void;
  onDeleteLibrary?: (id: string) => void;
}

export const LibraryList: React.FC<LibraryListProps> = ({
  onSelectLibrary,
  onEditLibrary,
  onDeleteLibrary,
}) => {
  const { data: libraries, isLoading, error } = useLibraries();

  if (isLoading) return <Spinner />;
  if (error) return <div>Error loading libraries</div>;
  if (!libraries || libraries.length === 0) return <div>No libraries found</div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--spacing-lg)' }}>
      {libraries.map((library) => (
        <LibraryCard
          key={library.id}
          library={library}
          onClick={onSelectLibrary}
          onEdit={onEditLibrary}
          onDelete={onDeleteLibrary}
        />
      ))}
    </div>
  );
};
