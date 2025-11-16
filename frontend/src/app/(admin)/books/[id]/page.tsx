'use client';

import { useParams } from 'next/navigation';
import { useBook } from '@/lib/hooks/useBooks';
import { useBlocks } from '@/lib/hooks/useBlocks';
import { BlockList } from '@/components/block';
import { Button } from '@/components/ui';
import { Skeleton } from '@/components/ui';
import Link from 'next/link';

/**
 * Book Detail Page
 * Displays a single book and its blocks
 * Route: /admin/books/{id}
 */
export default function BookDetailPage() {
  const params = useParams();
  const bookId = params.id as string;

  const { data: book, isLoading: isLoadingBook } = useBook(bookId);
  const { data: blocks, isLoading: isLoadingBlocks } = useBlocks(bookId);

  if (isLoadingBook) {
    return (
      <div className="space-y-4">
        <Skeleton height="2rem" width="30%" />
        <Skeleton height="1rem" width="50%" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} height="6rem" width="100%" />
          ))}
        </div>
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
      <div className="flex items-start justify-between">
        <div>
          <Link
            href={`/admin/bookshelves/${book.bookshelfId}`}
            className="text-sm text-blue-500 hover:underline mb-4 inline-block"
          >
            ← Back to Bookshelf
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            📖 {book.title}
          </h1>
          {book.description && (
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              {book.description}
            </p>
          )}
        </div>
        <Link href={`/admin/books/${bookId}/edit`}>
          <Button variant="primary">Edit Blocks</Button>
        </Link>
      </div>

      {/* Blocks Section */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          📝 Content ({blocks?.length ?? 0} blocks)
        </h2>
        {isLoadingBlocks ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="6rem" width="100%" />
            ))}
          </div>
        ) : blocks && blocks.length > 0 ? (
          <BlockList blocks={blocks} bookId={bookId} isLoading={false} />
        ) : (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">
              No content yet. Start editing to add blocks!
            </p>
            <Link href={`/admin/books/${bookId}/edit`}>
              <Button className="mt-4" variant="primary">
                Add Content
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
