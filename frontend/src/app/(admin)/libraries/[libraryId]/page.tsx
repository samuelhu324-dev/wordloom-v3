'use client'

import { useParams } from 'next/navigation'
import { BookshelfMainWidget } from '@/widgets/bookshelf'
import { Spinner } from '@/shared/ui'
import styles from './page.module.css'

// Mock data for development/testing
const MOCK_LIBRARY_DATA: Record<string, any> = {
  'test-123': {
    id: 'test-123',
    name: '我的书库',
    description: '这是一个测试书库，包含我收藏的所有书籍',
    user_id: 'user-1',
    basement_bookshelf_id: 'bs-basement',
    created_at: '2025-11-01T10:00:00Z',
    updated_at: '2025-11-16T15:00:00Z',
  },
}

const MOCK_BOOKSHELVES_DATA: Record<string, any[]> = {
  'test-123': [
    {
      id: 'bs-1',
      library_id: 'test-123',
      name: '阅读中',
      description: '正在阅读的书籍',
      created_at: '2025-11-01T10:00:00Z',
    },
    {
      id: 'bs-2',
      library_id: 'test-123',
      name: '已读',
      description: '已经读过的书籍',
      created_at: '2025-11-02T10:00:00Z',
    },
  ],
}

/**
 * Library Detail Page
 * Route: /admin/libraries/[libraryId]
 *
 * Displays all bookshelves within a specific library
 * - Fetch library metadata by ID
 * - List bookshelves in this library
 * - Allow create/edit/delete bookshelf operations
 */

export default function LibraryDetailPage() {
  const params = useParams()
  const libraryId = params.libraryId as string

  // Use mock data for development; in production, use real API
  const library = MOCK_LIBRARY_DATA[libraryId]
  const bookshelves = MOCK_BOOKSHELVES_DATA[libraryId] || []
  const isLoading = false
  const error = !library ? new Error('Library not found') : null

  if (isLoading) {
    return (
      <div className={styles.container}>
        <Spinner />
      </div>
    )
  }

  if (error || !library) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>无法加载书库</h2>
          <p>Library ID: {libraryId}</p>
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
        <span className={styles.active}>{library.name}</span>
      </div>

      {/* Header */}
      <div className={styles.header}>
        <h1>{library.name}</h1>
        <p className={styles.description}>{library.description}</p>
      </div>

      {/* Bookshelves List Widget */}
      <BookshelfMainWidget bookshelves={bookshelves} isLoading={isLoading} />
    </div>
  )
}
