/**
 * BookshelfList Component
 * Displays all bookshelves for a library with loading states
 */

'use client';

import { useState } from 'react';
import { useBookshelves, useDeleteBookshelf } from '@/lib/hooks';
import { BookshelfCard } from './BookshelfCard';
import { BookshelfForm } from './BookshelfForm';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { Card } from '@/components/ui/card';
import { useToast } from '@/lib/hooks/useToast';
import { useRouter } from 'next/navigation';
import type { BookshelfDto } from '@/lib/api/types';

interface BookshelfListProps {
  libraryId: string;
  bookshelves?: BookshelfDto[];
  isLoading?: boolean;
  onEdit?: (bookshelfId: string) => void;
}

/**
 * BookshelfList Component
 * Fetches and displays all bookshelves for a library
 * Includes loading skeleton, error state, and empty state
 */
export function BookshelfList({ libraryId }: BookshelfListProps) {
  const { data: bookshelves, isLoading, error } = useBookshelves(libraryId);
  const { mutate: deleteMutate, isPending: isDeleting } = useDeleteBookshelf(libraryId);
  const toast = useToast();
  const router = useRouter();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this bookshelf?')) {
      deleteMutate(id, {
        onSuccess: () => {
          toast.success({ message: 'Bookshelf deleted successfully' });
        },
        onError: (error: any) => {
          toast.error({
            message: 'Failed to delete bookshelf',
            description: error?.message || 'Please try again',
          });
        },
      });
    }
  };

  const handleView = (id: string) => {
    router.push(`/bookshelves/${id}`);
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
    toast.success({ message: 'Bookshelf saved successfully' });
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
        <h3 className="font-semibold text-red-900 dark:text-red-300">
          Failed to load bookshelves
        </h3>
        <p className="text-sm text-red-800 dark:text-red-400 mt-1">
          {error instanceof Error ? error.message : 'Please try again later'}
        </p>
      </Card>
    );
  }

  // Empty state
  if (!bookshelves || bookshelves.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400 mb-4">No bookshelves yet</p>
        <Button onClick={() => setShowForm(true)}>Create First Bookshelf</Button>
        {showForm && (
          <div className="mt-6">
            <BookshelfForm
              libraryId={libraryId}
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
          <BookshelfForm
            libraryId={libraryId}
            bookshelfId={editingId || undefined}
            onSuccess={handleFormSuccess}
            onCancel={handleFormClose}
          />
        </div>
      )}

      {/* Create Button */}
      {!showForm && (
        <Button onClick={() => setShowForm(true)}>Create New Bookshelf</Button>
      )}

      {/* Bookshelves Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bookshelves.map((bookshelf) => (
          <BookshelfCard
            key={bookshelf.id}
            bookshelf={bookshelf}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleView}
          />
        ))}
      </div>
    </div>
  );
}
