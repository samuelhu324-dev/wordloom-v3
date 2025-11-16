'use client'

import { useParams } from 'next/navigation'
import { BookMainWidget } from '@/widgets/book'
import { Spinner } from '@/shared/ui'
import styles from './page.module.css'

// Mock data for development/testing
const MOCK_BOOKSHELF_DATA: Record<string, any> = {
  'bs-1': {
    id: 'bs-1',
    library_id: 'test-123',
    name: '阅读中',
    description: '正在阅读的书籍',
    created_at: '2025-11-01T10:00:00Z',
  },
  'bs-2': {
    id: 'bs-2',
    library_id: 'test-123',
    name: '已读',
    description: '已经读过的书籍',
    created_at: '2025-11-02T10:00:00Z',
  },
}

const MOCK_BOOKS_DATA: Record<string, any[]> = {
  'bs-1': [
    {
      id: 'book-1',
      bookshelf_id: 'bs-1',
      title: '深入浅出 React',
      authors: ['Joe Haddad'],
      isbn: '978-1-234567-89-0',
      cover_url: 'https://via.placeholder.com/200x300?text=React',
      created_at: '2025-11-01T10:00:00Z',
    },
    {
      id: 'book-2',
      bookshelf_id: 'bs-1',
      title: 'Next.js 完全指南',
      authors: ['Lee Robinson'],
      isbn: '978-0-987654-32-1',
      cover_url: 'https://via.placeholder.com/200x300?text=Next.js',
      created_at: '2025-11-02T10:00:00Z',
    },
  ],
  'bs-2': [
    {
      id: 'book-3',
      bookshelf_id: 'bs-2',
      title: 'Clean Code',
      authors: ['Robert C. Martin'],
      isbn: '978-0-13-235088-4',
      cover_url: 'https://via.placeholder.com/200x300?text=Clean+Code',
      created_at: '2025-10-01T10:00:00Z',
    },
  ],
}

/**
 * Bookshelf Detail Page
 * Route: /admin/libraries/[libraryId]/bookshelves/[bookshelfId]
 *
 * Displays all books within a specific bookshelf
 * - Fetch bookshelf metadata by ID
 * - List books in this bookshelf
 * - Allow create/edit/delete book operations
 * - Show library name in breadcrumb
 */

export default function BookshelfDetailPage() {
  const params = useParams()
  const libraryId = params.libraryId as string
  const bookshelfId = params.bookshelfId as string

  // Use mock data for development
  const bookshelf = MOCK_BOOKSHELF_DATA[bookshelfId]
  const books = MOCK_BOOKS_DATA[bookshelfId] || []
  const isLoading = false
  const error = !bookshelf ? new Error('Bookshelf not found') : null

  if (isLoading) {
    return (
      <div className={styles.container}>
        <Spinner />
      </div>
    )
  }

  if (error || !bookshelf) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>无法加载书架</h2>
          <p>Bookshelf ID: {bookshelfId}</p>
          <p className={styles.errorMessage}>{error?.message || '未知错误'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Breadcrumb */}
      <div className={styles.breadcrumb}>
        <a href="/admin/libraries">书库列表</a>
        <span> / </span>
        <a href={`/admin/libraries/${libraryId}`}>书库详情</a>
        <span> / </span>
        <span className={styles.active}>{bookshelf.name}</span>
      </div>

      {/* Header */}
      <div className={styles.header}>
        <h1>{bookshelf.name}</h1>
        <p className={styles.description}>{bookshelf.description}</p>
      </div>

      {/* Books List Widget */}
      <BookMainWidget books={books} isLoading={isLoading} />
    </div>
  )
}
