'use client'

import { useParams } from 'next/navigation'
import { BlockMainWidget } from '@/widgets/block'
import { Spinner } from '@/shared/ui'
import styles from './page.module.css'

// Mock data for development/testing
const MOCK_BOOK_DATA: Record<string, any> = {
  'book-1': {
    id: 'book-1',
    bookshelf_id: 'bs-1',
    name: '深入浅出 React',
    title: '深入浅出 React',
    authors: ['Joe Haddad'],
    isbn: '978-1-234567-89-0',
    cover_url: 'https://via.placeholder.com/200x300?text=React',
    created_at: '2025-11-01T10:00:00Z',
  },
  'book-2': {
    id: 'book-2',
    bookshelf_id: 'bs-1',
    name: 'Next.js 完全指南',
    title: 'Next.js 完全指南',
    authors: ['Lee Robinson'],
    isbn: '978-0-987654-32-1',
    cover_url: 'https://via.placeholder.com/200x300?text=Next.js',
    created_at: '2025-11-02T10:00:00Z',
  },
}

const MOCK_BLOCKS_DATA: Record<string, any[]> = {
  'book-1': [
    {
      id: 'block-1',
      book_id: 'book-1',
      type: 'heading',
      content: 'Chapter 1: Getting Started',
      fractional_index: 'a0',
      created_at: '2025-11-01T10:00:00Z',
    },
    {
      id: 'block-2',
      book_id: 'book-1',
      type: 'text',
      content: 'React is a JavaScript library for building user interfaces with reusable components.',
      fractional_index: 'a1',
      created_at: '2025-11-01T10:05:00Z',
    },
    {
      id: 'block-3',
      book_id: 'book-1',
      type: 'heading',
      content: 'Chapter 2: Components',
      fractional_index: 'a2',
      created_at: '2025-11-01T10:10:00Z',
    },
    {
      id: 'block-4',
      book_id: 'book-1',
      type: 'text',
      content: 'Components are the building blocks of React applications.',
      fractional_index: 'a3',
      created_at: '2025-11-01T10:15:00Z',
    },
  ],
  'book-2': [
    {
      id: 'block-5',
      book_id: 'book-2',
      type: 'heading',
      content: 'Part 1: Next.js Basics',
      fractional_index: 'a0',
      created_at: '2025-11-02T10:00:00Z',
    },
    {
      id: 'block-6',
      book_id: 'book-2',
      type: 'text',
      content: 'Next.js is a React framework for production applications.',
      fractional_index: 'a1',
      created_at: '2025-11-02T10:05:00Z',
    },
  ],
}

/**
 * Book Detail Page (Block Editor)
 * Route: /admin/libraries/[libraryId]/bookshelves/[bookshelfId]/books/[bookId]
 *
 * Displays all blocks within a specific book
 */

export default function BookDetailPage() {
  const params = useParams()
  const libraryId = params.libraryId as string
  const bookshelfId = params.bookshelfId as string
  const bookId = params.bookId as string

  // Use mock data for development
  const book = MOCK_BOOK_DATA[bookId]
  const blocks = MOCK_BLOCKS_DATA[bookId] || []
  const isLoading = false
  const error = !book ? new Error('Book not found') : null

  if (isLoading) {
    return (
      <div className={styles.container}>
        <Spinner />
      </div>
    )
  }

  if (error || !book) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>无法加载书籍</h2>
          <p>Book ID: {bookId}</p>
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
        <a href={`/admin/libraries/${libraryId}`}>我的书库</a>
        <span> / </span>
        <a href={`/admin/libraries/${libraryId}/bookshelves/${bookshelfId}`}>阅读中</a>
        <span> / </span>
        <span className={styles.active}>{book.name}</span>
      </div>

      {/* Header */}
      <div className={styles.header}>
        <h1>{book.name}</h1>
        {book.description && <p className={styles.description}>{book.description}</p>}
      </div>

      {/* Blocks Editor Widget */}
      <BlockMainWidget blocks={blocks} isLoading={false} />
    </div>
  )
}
