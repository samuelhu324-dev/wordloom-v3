/**
 * BookCard Component
 * Displays a single book with action buttons
 */

'use client';

import { BookDto } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface BookCardProps {
  book: BookDto;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

/**
 * Single book card component
 * Shows book title, description, cover image, and action buttons
 * Clicking the card navigates to book detail page
 */
export function BookCard({ book, onEdit, onDelete, onView }: BookCardProps) {
  return (
    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer overflow-hidden">
      <div onClick={() => onView(book.id)} className="mb-3">
        {/* Cover Image */}
        {book.coverImageUrl && (
          <img
            src={book.coverImageUrl}
            alt={book.title}
            className="w-full h-32 object-cover rounded mb-3"
          />
        )}

        {/* Title & Description */}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white line-clamp-2">
          {book.title}
        </h3>
        {book.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
            {book.description}
          </p>
        )}

        {/* Metadata */}
        <div className="text-xs text-gray-500 dark:text-gray-500 mt-2 space-y-1">
          <div>Created: {new Date(book.createdAt).toLocaleDateString()}</div>
          {book.isArchived && (
            <div className="text-amber-600 dark:text-amber-400 font-medium">Archived</div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(book.id);
          }}
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(book.id);
          }}
        >
          Delete
        </Button>
      </div>
    </Card>
  );
}
