/**
 * BookshelfForm Component
 * Form for creating/editing a bookshelf
 */

'use client';

import { useState, useEffect } from 'react';
import { useCreateBookshelf, useUpdateBookshelf, useBookshelf } from '@/lib/hooks';
import { CreateBookshelfRequest, UpdateBookshelfRequest } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Spinner } from '@/components/ui/spinner';

interface BookshelfFormProps {
  libraryId: string;
  bookshelfId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

/**
 * BookshelfForm Component
 * Create new bookshelf or edit existing one
 * Includes form validation and error handling
 */
export function BookshelfForm({
  libraryId,
  bookshelfId,
  onSuccess,
  onCancel,
}: BookshelfFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [error, setError] = useState<string | null>(null);

  const { data: existingBookshelf, isLoading: isFetching } = useBookshelf(
    bookshelfId || ''
  );
  const { mutate: createMutate, isPending: isCreating } = useCreateBookshelf(libraryId);
  const { mutate: updateMutate, isPending: isUpdating } = useUpdateBookshelf(libraryId);

  // Load existing bookshelf data
  useEffect(() => {
    if (existingBookshelf) {
      setFormData({
        name: existingBookshelf.name,
        description: existingBookshelf.description || '',
      });
    }
  }, [existingBookshelf]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.name.trim()) {
      setError('Name is required');
      return;
    }

    if (bookshelfId) {
      // Update mode
      const request: UpdateBookshelfRequest = {
        name: formData.name,
        description: formData.description || undefined,
      };
      updateMutate(
        { id: bookshelfId, request },
        {
          onError: (err: any) => {
            setError(err?.message || 'Failed to update bookshelf');
          },
          onSuccess: () => {
            onSuccess();
          },
        }
      );
    } else {
      // Create mode
      const request: CreateBookshelfRequest = {
        name: formData.name,
        description: formData.description || undefined,
      };
      createMutate(request, {
        onError: (err: any) => {
          setError(err?.message || 'Failed to create bookshelf');
        },
        onSuccess: () => {
          onSuccess();
        },
      });
    }
  };

  const isLoading = isFetching || isCreating || isUpdating;
  const isEdit = !!bookshelfId;

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold mb-4">
        {isEdit ? 'Edit Bookshelf' : 'Create New Bookshelf'}
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-900 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Name *
          </label>
          <Input
            type="text"
            placeholder="e.g., My Fiction Books"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
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
      </div>

      <div className="flex gap-3 mt-6">
        <Button type="submit" disabled={isLoading}>
          {isLoading && <Spinner className="mr-2" />}
          {isEdit ? 'Update Bookshelf' : 'Create Bookshelf'}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
