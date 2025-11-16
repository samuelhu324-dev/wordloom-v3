/**
 * BookForm Component
 * Form for creating/editing a book
 */

'use client';

import { useState, useEffect } from 'react';
import { useCreateBook, useUpdateBook, useBook } from '@/lib/hooks';
import { CreateBookRequest, UpdateBookRequest } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Spinner } from '@/components/ui/spinner';

interface BookFormProps {
  bookshelfId: string;
  bookId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

/**
 * BookForm Component
 * Create new book or edit existing one
 * Includes form validation and error handling
 */
export function BookForm({ bookshelfId, bookId, onSuccess, onCancel }: BookFormProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    coverImageUrl: '',
  });
  const [error, setError] = useState<string | null>(null);

  const { data: existingBook, isLoading: isFetching } = useBook(bookId || '');
  const { mutate: createMutate, isPending: isCreating } = useCreateBook(bookshelfId);
  const { mutate: updateMutate, isPending: isUpdating } = useUpdateBook(bookshelfId);

  // Load existing book data
  useEffect(() => {
    if (existingBook) {
      setFormData({
        title: existingBook.title,
        description: existingBook.description || '',
        coverImageUrl: existingBook.coverImageUrl || '',
      });
    }
  }, [existingBook]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    if (bookId) {
      // Update mode
      const request: UpdateBookRequest = {
        title: formData.title,
        description: formData.description || undefined,
        coverImageUrl: formData.coverImageUrl || undefined,
      };
      updateMutate(
        { id: bookId, request },
        {
          onError: (err: any) => {
            setError(err?.message || 'Failed to update book');
          },
          onSuccess: () => {
            onSuccess();
          },
        }
      );
    } else {
      // Create mode
      const request: CreateBookRequest = {
        bookshelfId,
        title: formData.title,
        description: formData.description || undefined,
        coverImageUrl: formData.coverImageUrl || undefined,
      };
      createMutate(request, {
        onError: (err: any) => {
          setError(err?.message || 'Failed to create book');
        },
        onSuccess: () => {
          onSuccess();
        },
      });
    }
  };

  const isLoading = isFetching || isCreating || isUpdating;
  const isEdit = !!bookId;

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold mb-4">
        {isEdit ? 'Edit Book' : 'Create New Book'}
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-900 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Title *
          </label>
          <Input
            type="text"
            placeholder="e.g., My Adventure Book"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            disabled={isLoading}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            placeholder="Optional description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            disabled={isLoading}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Cover Image URL
          </label>
          <Input
            type="url"
            placeholder="https://example.com/cover.jpg"
            value={formData.coverImageUrl}
            onChange={(e) => setFormData({ ...formData, coverImageUrl: e.target.value })}
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="flex gap-3 mt-6">
        <Button type="submit" disabled={isLoading}>
          {isLoading && <Spinner className="mr-2" />}
          {isEdit ? 'Update Book' : 'Create Book'}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
