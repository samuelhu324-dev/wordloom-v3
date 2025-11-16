/**
 * BookshelfCard Component
 * Displays a single bookshelf with action buttons
 */

'use client';

import { BookshelfDto } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface BookshelfCardProps {
  bookshelf: BookshelfDto;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

/**
 * Single bookshelf card component
 * Shows bookshelf name, description, and action buttons
 * Clicking the card navigates to bookshelf detail page
 */
export function BookshelfCard({
  bookshelf,
  onEdit,
  onDelete,
  onView,
}: BookshelfCardProps) {
  return (
    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
      <div onClick={() => onView(bookshelf.id)} className="mb-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {bookshelf.name}
        </h3>
        {bookshelf.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
            {bookshelf.description}
          </p>
        )}
        <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">
          Created: {new Date(bookshelf.createdAt).toLocaleDateString()}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(bookshelf.id);
          }}
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(bookshelf.id);
          }}
        >
          Delete
        </Button>
      </div>
    </Card>
  );
}
