'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LibraryMainWidget } from '@/widgets/library';
import styles from './page.module.css';

/**
 * Libraries List Page
 * Route: /admin/libraries
 *
 * Displays all libraries for the current user
 * - List all libraries with optional search query from URL (?q=)
 * - Create new library
 * - Navigate to library detail
 */
export default function LibrariesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchQuery = searchParams?.get('q') || '';

  const handleSelectLibrary = (libraryId: string) => {
    router.push(`/admin/libraries/${libraryId}`);
  };

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <LibraryMainWidget
          onSelectLibrary={handleSelectLibrary}
          searchQuery={searchQuery}
        />
      </div>
    </main>
  );
}
