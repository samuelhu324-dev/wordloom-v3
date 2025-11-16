'use client';

import { useParams } from 'next/navigation';
import { useBookshelf } from '@/lib/hooks/useBookshelves';
import { useBooks } from '@/lib/hooks/useBooks';
import { BookList } from '@/components/book';
import { Skeleton } from '@/components/ui';
import Link from 'next/link';

/**
 * Bookshelf Detail Page
 * Displays a single bookshelf and its books
 * Route: /admin/bookshelves/{id}
 */
export default function BookshelfDetailPage() {
  const params = useParams();
  const bookshelfId = params.id as string;

  const { data: bookshelf, isLoading: isLoadingBookshelf } =
    useBookshelf(bookshelfId);
  const { data: books, isLoading: isLoadingBooks } = useBooks(bookshelfId);

  if (isLoadingBookshelf) {
    return (
      <div className="space-y-4">
        <Skeleton height="2rem" width="30%" />
        <Skeleton height="1rem" width="50%" />
        <div className="grid grid-cols-auto gap-lg">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} height="12rem" width="100%" />
          ))}
        </div>
      </div>
    );
  }

  if (!bookshelf) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Bookshelf not found</p>
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
          href={`/admin/libraries/${bookshelf.libraryId}`}
          className="text-sm text-blue-500 hover:underline mb-4 inline-block"
        >
          ← Back to Library
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          📚 {bookshelf.name}
        </h1>
        {bookshelf.description && (
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {bookshelf.description}
          </p>
        )}
      </div>

      {/* Books Section */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          📖 Books ({books?.length ?? 0})
        </h2>
        {isLoadingBooks ? (
          <div className="grid grid-cols-auto gap-lg">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="12rem" width="100%" />
            ))}
          </div>
        ) : books && books.length > 0 ? (
          <BookList books={books} bookshelfId={bookshelfId} isLoading={false} />
        ) : (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">
              No books yet. Add one to get started!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
