/**
 * BookList Component
 * Displays all books in a bookshelf with loading states
 */

'use client';

import { useState } from 'react';
import { useBooks, useDeleteBook } from '@/lib/hooks';
import { BookCard } from './BookCard';
import { BookForm } from './BookForm';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/spinner';
import { Card } from '@/components/ui/card';
import { useToast } from '@/lib/hooks/useToast';
import { useRouter } from 'next/navigation';
import type { BookDto } from '@/lib/api/types';

interface BookListProps {
  bookshelfId: string;
  books?: BookDto[];
  includeArchived?: boolean;
  isLoading?: boolean;
  onEdit?: (bookId: string) => void;
}

/**
 * BookList Component
 * Fetches and displays all books for a bookshelf
 * Includes loading skeleton, error state, and empty state
 */
export function BookList({ bookshelfId, includeArchived = false }: BookListProps) {
  const { data: books, isLoading, error } = useBooks(bookshelfId, includeArchived);
  const { mutate: deleteMutate, isPending: isDeleting } = useDeleteBook(bookshelfId);
  const toast = useToast();
  const router = useRouter();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this book?')) {
      deleteMutate(id, {
        onSuccess: () => {
          toast.success({ message: 'Book deleted successfully' });
        },
        onError: (error: any) => {
          toast.error({
            message: 'Failed to delete book',
            description: error?.message || 'Please try again',
          });
        },
      });
    }
  };

  const handleView = (id: string) => {
    router.push(`/books/${id}`);
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
    toast.success({ message: 'Book saved successfully' });
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
        <h3 className="font-semibold text-red-900 dark:text-red-300">Failed to load books</h3>
        <p className="text-sm text-red-800 dark:text-red-400 mt-1">
          {error instanceof Error ? error.message : 'Please try again later'}
        </p>
      </Card>
    );
  }

  // Empty state
  if (!books || books.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400 mb-4">No books yet</p>
        <Button onClick={() => setShowForm(true)}>Create First Book</Button>
        {showForm && (
          <div className="mt-6">
            <BookForm
              bookshelfId={bookshelfId}
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
          <BookForm
            bookshelfId={bookshelfId}
            bookId={editingId || undefined}
            onSuccess={handleFormSuccess}
            onCancel={handleFormClose}
          />
        </div>
      )}

      {/* Create Button */}
      {!showForm && <Button onClick={() => setShowForm(true)}>Create New Book</Button>}

      {/* Books Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleView}
          />
        ))}
      </div>
    </div>
  );
}
