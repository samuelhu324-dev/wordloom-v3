/**
 * BlockEditor Component
 * Edit blocks with drag-drop and rich content support
 */

'use client';

import React, { useState } from 'react';
import { BlockCard } from './BlockCard';
import { BlockForm } from './BlockForm';
import { Spinner } from '@/components/ui';
import type { BlockDto } from '@/lib/api/types';

interface BlockEditorProps {
  bookId: string;
  blocks?: BlockDto[];
  isLoading?: boolean;
  onSave?: () => void;
}

export function BlockEditor({ bookId, isLoading = false, onSave }: BlockEditorProps) {
  const [editingBlockId, setEditingBlockId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Block Editor</h2>
      </div>

      {editingBlockId ? (
        <BlockForm
          bookId={bookId}
          blockId={editingBlockId}
          onCancel={() => setEditingBlockId(null)}
          onSave={() => {
            setEditingBlockId(null);
            onSave?.();
          }}
        />
      ) : (
        <BlockList
          bookId={bookId}
          onEdit={setEditingBlockId}
        />
      )}
    </div>
  );
}
