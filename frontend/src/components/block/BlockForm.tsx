/**
 * BlockForm Component
 * Form for creating/editing a block
 */

'use client';

import { useState, useEffect } from 'react';
import { useCreateBlock, useUpdateBlock, useBlock } from '@/lib/hooks';
import { CreateBlockRequest, UpdateBlockRequest } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Spinner } from '@/components/ui/spinner';

interface BlockFormProps {
  bookId: string;
  blockId?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

/**
 * BlockForm Component
 * Create new block or edit existing one
 * Includes form validation and error handling
 */
export function BlockForm({ bookId, blockId, onSuccess, onCancel }: BlockFormProps) {
  const [formData, setFormData] = useState({
    type: 'markdown' as const,
    content: '',
  });
  const [error, setError] = useState<string | null>(null);

  const { data: existingBlock, isLoading: isFetching } = useBlock(blockId || '');
  const { mutate: createMutate, isPending: isCreating } = useCreateBlock(bookId);
  const { mutate: updateMutate, isPending: isUpdating } = useUpdateBlock(bookId);

  // Load existing block data
  useEffect(() => {
    if (existingBlock) {
      setFormData({
        type: existingBlock.type,
        content: existingBlock.content,
      });
    }
  }, [existingBlock]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.content.trim()) {
      setError('Content is required');
      return;
    }

    if (blockId) {
      // Update mode
      const request: UpdateBlockRequest = {
        type: formData.type,
        content: formData.content,
      };
      updateMutate(
        { id: blockId, request },
        {
          onError: (err: any) => {
            setError(err?.message || 'Failed to update block');
          },
          onSuccess: () => {
            onSuccess();
          },
        }
      );
    } else {
      // Create mode
      const request: CreateBlockRequest = {
        bookId,
        type: formData.type,
        content: formData.content,
      };
      createMutate(request, {
        onError: (err: any) => {
          setError(err?.message || 'Failed to create block');
        },
        onSuccess: () => {
          onSuccess();
        },
      });
    }
  };

  const isLoading = isFetching || isCreating || isUpdating;
  const isEdit = !!blockId;

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white dark:bg-gray-900 p-6 rounded-lg border border-gray-200 dark:border-gray-700"
    >
      <h3 className="text-lg font-semibold mb-4">
        {isEdit ? 'Edit Block' : 'Create New Block'}
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-900 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Block Type *
          </label>
          <select
            value={formData.type}
            onChange={(e) =>
              setFormData({
                ...formData,
                type: e.target.value as 'markdown' | 'heading' | 'image' | 'video',
              })
            }
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="markdown">Markdown</option>
            <option value="heading">Heading</option>
            <option value="image">Image</option>
            <option value="video">Video</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Content *
          </label>
          <textarea
            placeholder={
              formData.type === 'markdown'
                ? 'Enter markdown content'
                : 'Enter content URL or description'
            }
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            disabled={isLoading}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
      </div>

      <div className="flex gap-3 mt-6">
        <Button type="submit" disabled={isLoading}>
          {isLoading && <Spinner className="mr-2" />}
          {isEdit ? 'Update Block' : 'Create Block'}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
