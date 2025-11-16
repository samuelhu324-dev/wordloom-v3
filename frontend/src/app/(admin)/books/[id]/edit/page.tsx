'use client';

import { useParams } from 'next/navigation';
import { useBook } from '@/lib/hooks/useBooks';
import { useBlocks } from '@/lib/hooks/useBlocks';
import { BlockEditor } from '@/components/block';
import { Skeleton } from '@/components/ui';
import Link from 'next/link';

/**
 * Block Editor Page
 * Editable interface for managing book blocks (content)
 * Route: /admin/books/{id}/edit
 *
 * Features:
 * - Add/edit/delete blocks
 * - Drag-and-drop reordering (via BlockEditor)
 * - Real-time preview
 * - Auto-save via mutations
 */
export default function BlockEditPage() {
  const params = useParams();
  const bookId = params.id as string;

  const { data: book, isLoading: isLoadingBook } = useBook(bookId);
  const { data: blocks, isLoading: isLoadingBlocks } = useBlocks(bookId);

  if (isLoadingBook) {
    return (
      <div className="space-y-4">
        <Skeleton height="2rem" width="30%" />
        <Skeleton height="20rem" width="100%" />
      </div>
    );
  }

  if (!book) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Book not found</p>
        <Link href="/admin/dashboard" className="text-blue-500 hover:underline mt-4">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <Link
          href={`/admin/books/${bookId}`}
          className="text-sm text-blue-500 hover:underline mb-4 inline-block"
        >
          ← Back to Book
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          ✏️ Edit: {book.title}
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage your book content - add, edit, reorder, and delete blocks
        </p>
      </div>

      {/* Block Editor */}
      {isLoadingBlocks ? (
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} height="8rem" width="100%" />
          ))}
        </div>
      ) : (
        <BlockEditor bookId={bookId} blocks={blocks || []} />
      )}
    </div>
  );
}
