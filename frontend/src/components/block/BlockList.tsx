/**
 * BlockList Component
 * Displays all blocks in a book with loading states
 */

'use client';

import { useState } from 'react';
import { useBlocks, useDeleteBlock } from '@/lib/hooks';
import { BlockCard } from './BlockCard';
import { BlockForm } from './BlockForm';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { Card } from '@/components/ui/card';
import { useToast } from '@/lib/hooks/useToast';
import type { BlockDto } from '@/lib/api/types';

interface BlockListProps {
  bookId: string;
  blocks?: BlockDto[];
  isLoading?: boolean;
  onEdit?: (blockId: string) => void;
}

/**
 * BlockList Component
 * Fetches and displays all blocks for a book
 * Blocks are ordered by fractionalIndex (Fractional Index Ordering - RULE-015)
 * Includes loading skeleton, error state, and empty state
 */
export function BlockList({ bookId }: BlockListProps) {
  const { data: blocks, isLoading, error } = useBlocks(bookId);
  const { mutate: deleteMutate, isPending: isDeleting } = useDeleteBlock(bookId);
  const toast = useToast();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this block?')) {
      deleteMutate(id, {
        onSuccess: () => {
          toast.success({ message: 'Block deleted successfully' });
        },
        onError: (error: any) => {
          toast.error({
            message: 'Failed to delete block',
            description: error?.message || 'Please try again',
          });
        },
      });
    }
  };

  const handleEdit = (id: string) => {
    setEditingId(id);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingId(null);
  };

  const handleFormSuccess = () => {
    handleFormClose();
    toast.success({ message: 'Block saved successfully' });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Spinner />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="p-6 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
        <h3 className="font-semibold text-red-900 dark:text-red-300">Failed to load blocks</h3>
        <p className="text-sm text-red-800 dark:text-red-400 mt-1">
          {error instanceof Error ? error.message : 'Please try again later'}
        </p>
      </Card>
    );
  }

  // Empty state
  if (!blocks || blocks.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400 mb-4">No blocks yet</p>
        <Button onClick={() => setShowForm(true)}>Create First Block</Button>
        {showForm && (
          <div className="mt-6">
            <BlockForm
              bookId={bookId}
              onSuccess={handleFormSuccess}
              onCancel={handleFormClose}
            />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Create/Edit Form */}
      {showForm && (
        <div className="mb-6">
          <BlockForm
            bookId={bookId}
            blockId={editingId || undefined}
            onSuccess={handleFormSuccess}
            onCancel={handleFormClose}
          />
        </div>
      )}

      {/* Create Button */}
      {!showForm && <Button onClick={() => setShowForm(true)}>Create New Block</Button>}

      {/* Blocks List (not grid, since order matters) */}
      <div className="space-y-4">
        {blocks.map((block) => (
          <BlockCard
            key={block.id}
            block={block}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleEdit}
          />
        ))}
      </div>
    </div>
  );
}
