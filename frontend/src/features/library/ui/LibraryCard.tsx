'use client';

import React from 'react';
import { LibraryDto } from '@/entities/library';
import { Card, CardContent, CardHeader, Button } from '@/shared/ui';

export interface LibraryCardProps {
  library: LibraryDto;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onClick?: (id: string) => void;
}

export const LibraryCard: React.FC<LibraryCardProps> = ({
  library,
  onEdit,
  onDelete,
  onClick,
}) => {
  return (
    <Card
      style={{ cursor: onClick ? 'pointer' : 'default' }}
      onClick={() => onClick?.(library.id)}
    >
      <CardHeader>
        <h3>{library.name}</h3>
      </CardHeader>
      <CardContent>
        {library.description && <p>{library.description}</p>}
        <small style={{ color: 'var(--color-text-muted)' }}>
          Created {new Date(library.created_at).toLocaleDateString()}
        </small>
      </CardContent>
      <div style={{ padding: 'var(--spacing-lg)', display: 'flex', gap: 'var(--spacing-md)' }}>
        {onEdit && (
          <Button size="sm" variant="secondary" onClick={() => onEdit(library.id)}>
            Edit
          </Button>
        )}
        {onDelete && (
          <Button size="sm" variant="danger" onClick={() => onDelete(library.id)}>
            Delete
          </Button>
        )}
      </div>
    </Card>
  );
};
