'use client';

import { useParams } from 'next/navigation';
import { useLibraries } from '@/lib/hooks/useLibraries';
import { useBookshelves } from '@/lib/hooks/useBookshelves';
import { BookshelfList } from '@/components/bookshelf';
import { Skeleton } from '@/components/ui';
import Link from 'next/link';

/**
 * Library Detail Page
 * Displays a single library and its bookshelves
 * Route: /admin/libraries/{id}
 */
export default function LibraryDetailPage() {
  const params = useParams();
  const libraryId = params.id as string;

  const { data: libraries, isLoading: isLoadingLibraries } = useLibraries();
  const { data: bookshelves, isLoading: isLoadingBookshelves } =
    useBookshelves(libraryId);

  // Find current library
  const currentLibrary = libraries?.find((lib) => lib.id === libraryId);

  if (isLoadingLibraries) {
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

  if (!currentLibrary) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Library not found</p>
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
          href="/admin/dashboard"
          className="text-sm text-blue-500 hover:underline mb-4 inline-block"
        >
          ← Back to Libraries
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          📚 {currentLibrary.name}
        </h1>
        {currentLibrary.description && (
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {currentLibrary.description}
          </p>
        )}
      </div>

      {/* Bookshelves Section */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          📖 Bookshelves ({bookshelves?.length ?? 0})
        </h2>
        {isLoadingBookshelves ? (
          <div className="grid grid-cols-auto gap-lg">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="12rem" width="100%" />
            ))}
          </div>
        ) : bookshelves && bookshelves.length > 0 ? (
          <BookshelfList
            bookshelves={bookshelves}
            libraryId={libraryId}
            isLoading={false}
          />
        ) : (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400">
              No bookshelves yet. Create one to get started!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
