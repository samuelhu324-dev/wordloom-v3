/**
 * BlockCard Component
 * Displays a single block with action buttons
 */

'use client';

import { BlockDto } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface BlockCardProps {
  block: BlockDto;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

/**
 * Single block card component
 * Shows block type, content preview, and action buttons
 * Clicking the card navigates to block detail or edit
 */
export function BlockCard({ block, onEdit, onDelete, onView }: BlockCardProps) {
  // Get content preview (limit to 100 chars)
  const preview = block.content.substring(0, 100).replace(/\n/g, ' ');
  const hasMore = block.content.length > 100;

  // Get type badge color
  const typeColor = {
    markdown: 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100',
    heading: 'bg-purple-100 dark:bg-purple-900 text-purple-900 dark:text-purple-100',
    image: 'bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
    video: 'bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  }[block.type] || 'bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100';

  return (
    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
      <div onClick={() => onView(block.id)} className="mb-3">
        {/* Type Badge */}
        <div className="inline-block mb-2">
          <span
            className={`inline-block px-2 py-1 rounded text-xs font-semibold ${typeColor}`}
          >
            {block.type.toUpperCase()}
          </span>
        </div>

        {/* Content Preview */}
        <p className="text-sm text-gray-700 dark:text-gray-300">
          {preview}
          {hasMore && '...'}
        </p>

        {/* Metadata */}
        <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">
          Updated: {new Date(block.updatedAt).toLocaleDateString()}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(block.id);
          }}
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(block.id);
          }}
        >
          Delete
        </Button>
      </div>
    </Card>
  );
}
