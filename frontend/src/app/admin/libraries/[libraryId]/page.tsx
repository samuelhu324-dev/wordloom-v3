'use client'

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from 'react'
import { useParams, useRouter, notFound } from 'next/navigation'
import type { AxiosError } from 'axios'
import { Spinner, Breadcrumb, Button } from '@/shared/ui'
import { showToast } from '@/shared/ui/toast'
import {
  useLibrary,
  useLibraryThemeColor,
  LibraryForm,
  type LibraryFormSubmitPayload,
  type LibraryFormTagValue,
} from '@/features/library'
import { DEFAULT_TAG_COLOR } from '@/features/library/constants'
import { BookshelfDashboardBoard, useCreateBookshelf } from '@/features/bookshelf'
import { useI18n } from '@/i18n/useI18n'
import type {
  BookshelfDashboardFilter,
  BookshelfDashboardSort,
  BookshelfDashboardItemDto,
  BookshelfDashboardSnapshot,
  CreateBookshelfRequest,
} from '@/entities/bookshelf'
import { createTag as createGlobalTag, searchTags as searchGlobalTags } from '@/features/tag/model/api'
import styles from './page.module.css'
/**
 * Library Detail Page
 * Route: /admin/libraries/[libraryId]
 *
 * Displays all bookshelves within a specific library
 * - Fetch library metadata by ID
 * - 展示书架运营看板（排序 / 筛选 / 视图切换）
 * - 集中展示书架健康度、Pinned 数等指标
 * - Breadcrumb 导航回书库列表
 */

const SORT_OPTIONS: BookshelfDashboardSort[] = ['recent_activity', 'name_asc', 'created_desc', 'book_count_desc']
const FILTER_OPTIONS: BookshelfDashboardFilter[] = ['active', 'all', 'archived']
const DEFAULT_SORT: BookshelfDashboardSort = 'recent_activity'
const DEFAULT_FILTER: BookshelfDashboardFilter = 'active'

const MAX_BOOKSHELVES = 100
const WARN_THRESHOLD = 80
const TAG_LIMIT = 3

const EMPTY_SNAPSHOT: BookshelfDashboardSnapshot = {
  total: 0,
  pinned: 0,
  health: { active: 0, slowing: 0, cooling: 0, archived: 0 },
}

function normalizeTagSelections(tags: LibraryFormTagValue[] = []): LibraryFormTagValue[] {
  const normalized: LibraryFormTagValue[] = []
  const seen = new Set<string>()
  for (const tag of tags ?? []) {
    const trimmed = (tag.name || '').trim()
    if (!trimmed) continue
    const key = tag.id || trimmed.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    normalized.push({
      ...tag,
      name: trimmed,
    })
    if (normalized.length >= TAG_LIMIT) break
  }
  return normalized
}

async function ensureTagIds(tags: LibraryFormTagValue[] = []): Promise<string[]> {
  const ids: string[] = []
  for (const tag of tags) {
    if (tag.id) {
      ids.push(tag.id)
      continue
    }
    const resolvedName = (tag.name || '').trim()
    if (!resolvedName) {
      continue
    }
    ids.push(await resolveTagId(resolvedName))
  }
  return ids
}

async function resolveTagId(name: string): Promise<string> {
  try {
    const created = await createGlobalTag({ name, color: DEFAULT_TAG_COLOR })
    return created.id
  } catch (error) {
    if (isConflictError(error)) {
      const matches = await searchGlobalTags({ keyword: name, limit: 5 })
      const exact = matches.find((tag) => tag.name?.trim().toLowerCase() === name.trim().toLowerCase())
      if (exact?.id) {
        return exact.id
      }
    }
    throw error
  }
}

function extractApiErrorMessage(error: unknown): string {
  const detail = (error as any)?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        const loc = Array.isArray(item?.loc) ? item.loc.join('.') : item?.loc
        const msg = item?.msg || item?.message || ''
        return loc ? `${loc}: ${msg}` : msg || JSON.stringify(item ?? {})
      })
      .filter(Boolean)
      .join(' | ')
  }
  if (typeof detail === 'string') return detail
  if (detail?.message) return detail.message
  const message = (error as Error)?.message
  return message || '未知错误'
}

function isConflictError(error: unknown): error is AxiosError<any> {
  const axiosError = error as AxiosError<any> | undefined
  return Boolean(axiosError?.response && axiosError.response.status === 409)
}

function coerceSort(value: string | null): BookshelfDashboardSort {
  return SORT_OPTIONS.includes(value as BookshelfDashboardSort) ? (value as BookshelfDashboardSort) : DEFAULT_SORT
}

function coerceFilter(value: string | null): BookshelfDashboardFilter {
  return FILTER_OPTIONS.includes(value as BookshelfDashboardFilter) ? (value as BookshelfDashboardFilter) : DEFAULT_FILTER
}

export default function LibraryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const libraryId = (params.libraryId as string) || ''
  const { t } = useI18n()

  const { data: library, isLoading: isLibraryLoading, error: libraryError, refetch: refetchLibrary } = useLibrary(libraryId)

  const [cachedLibrary, setCachedLibrary] = useState<any | null>(null)
  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      const raw = localStorage.getItem(`wl_library_cache_${libraryId}`)
      if (!raw) {
        setCachedLibrary(null)
        return
      }
      const parsed = JSON.parse(raw)
      if (parsed && typeof parsed === 'object' && parsed.data) {
        setCachedLibrary(parsed.data)
      } else {
        setCachedLibrary(parsed)
      }
    } catch {
      setCachedLibrary(null)
    }
  }, [libraryId])

  useEffect(() => {
    if (library) {
      setCachedLibrary(library)
    }
  }, [library])

  // 首屏加载判断（无缓存且在加载中）
  const isInitialLoading = isLibraryLoading && !cachedLibrary && !library

  // 如果后端明确返回 404，调用 notFound 渲染专属页面
  useEffect(() => {
    const status = (libraryError as any)?.response?.status
    if (!isLibraryLoading && status === 404) {
      notFound()
    }
  }, [isLibraryLoading, libraryError])

  const [sort, setSort] = useState<BookshelfDashboardSort>(DEFAULT_SORT)
  const [statusFilter, setStatusFilter] = useState<BookshelfDashboardFilter>(DEFAULT_FILTER)
  useEffect(() => {
    if (!libraryId || typeof window === 'undefined') return
    try {
      const storedSort = localStorage.getItem(`wl_bs_sort_${libraryId}`)
      const storedFilter = localStorage.getItem(`wl_bs_filter_${libraryId}`)
      setSort(coerceSort(storedSort))
      setStatusFilter(coerceFilter(storedFilter))
    } catch {}
  }, [libraryId])

  useEffect(() => {
    if (!libraryId || typeof window === 'undefined') return
    try {
      localStorage.setItem(`wl_bs_sort_${libraryId}`, sort)
      localStorage.setItem(`wl_bs_filter_${libraryId}`, statusFilter)
    } catch {}
  }, [libraryId, sort, statusFilter])

  const [snapshot, setSnapshot] = useState<BookshelfDashboardSnapshot>(EMPTY_SNAPSHOT)
  const { mutateAsync: createBookshelfAsync, isPending: isCreatePending } = useCreateBookshelf()
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isCreateDialogSaving, setIsCreateDialogSaving] = useState(false)

  const handleSnapshotChange = useCallback((next: BookshelfDashboardSnapshot) => {
    setSnapshot((current) => {
      if (
        current.total === next.total &&
        current.pinned === next.pinned &&
        current.health.active === next.health.active &&
        current.health.slowing === next.health.slowing &&
        current.health.cooling === next.health.cooling &&
        current.health.archived === next.health.archived
      ) {
        return current
      }
      return next
    })
  }, [])

  const libraryTheme = useLibraryThemeColor({
    libraryId,
    libraryName: library?.name || cachedLibrary?.name,
    coverUrl: library?.coverUrl || cachedLibrary?.coverUrl,
    themeColor: library?.theme_color ?? cachedLibrary?.theme_color ?? null,
  })

  const libraryThemeVars = useMemo(() => ({
    '--lib-h': String(libraryTheme.h),
    '--lib-s': `${libraryTheme.s}%`,
    '--lib-l': `${libraryTheme.l}%`,
    '--lib-hex': libraryTheme.hex,
  }) as CSSProperties, [libraryTheme])

  const progressPercentage = Math.min(100, snapshot.total === 0 ? 0 : (snapshot.total / MAX_BOOKSHELVES) * 100)
  const showProgress = snapshot.total >= WARN_THRESHOLD
  const limitMessage = snapshot.total >= MAX_BOOKSHELVES
    ? t('bookshelves.library.progress.limitReached')
    : t('bookshelves.library.progress.nearLimit')

  const summaryBadges = useMemo(() => ([
    { label: t('bookshelves.library.summary.pinned'), value: snapshot.pinned },
    { label: t('bookshelves.library.summary.active'), value: snapshot.health.active },
    { label: t('bookshelves.library.summary.slowing'), value: snapshot.health.slowing },
    { label: t('bookshelves.library.summary.cooling'), value: snapshot.health.cooling },
    { label: t('bookshelves.library.summary.archived'), value: snapshot.health.archived },
  ]), [snapshot, t])

  const totalBookshelves = snapshot.total
  const isCreateDialogLoading = isCreateDialogSaving || isCreatePending

  const handleOpenBookshelf = useCallback((item: BookshelfDashboardItemDto) => {
    router.push(`/admin/bookshelves/${item.id}`)
  }, [router])

  const handleCreateBookshelf = useCallback(() => {
    if (!libraryId) return
    if (totalBookshelves >= MAX_BOOKSHELVES) {
      showToast(t('bookshelves.library.toast.limitReached'))
      return
    }
    setIsCreateDialogOpen(true)
  }, [libraryId, totalBookshelves])

  const handleCreateDialogClose = useCallback(() => {
    if (isCreateDialogLoading) return
    setIsCreateDialogOpen(false)
  }, [isCreateDialogLoading])

  const handleCreateDialogSubmit = useCallback(async ({ formValues, tags }: LibraryFormSubmitPayload) => {
    if (!libraryId) return
    setIsCreateDialogSaving(true)
    try {
      const normalizedTags = normalizeTagSelections(tags)
      const tagIds = await ensureTagIds(normalizedTags)
      const payload: CreateBookshelfRequest = {
        name: formValues.name,
        description: formValues.description,
        library_id: libraryId,
      }
      if (tagIds.length > 0) {
        payload.tag_ids = tagIds
      }

      await createBookshelfAsync(payload)
      showToast(t('bookshelves.library.toast.createSuccess'))
      setIsCreateDialogOpen(false)
    } catch (error) {
      console.error('创建书橱失败:', error)
      const message = extractApiErrorMessage(error)
      showToast(t('bookshelves.library.toast.createFailed', { message }))
    } finally {
      setIsCreateDialogSaving(false)
    }
  }, [createBookshelfAsync, libraryId])

  // 显示首屏 spinner（仅当完全无数据时）
  if (isInitialLoading) {
    return <div className={styles.container}><Spinner /></div>
  }

  const resolvedName = (library?.name ?? cachedLibrary?.name) || ''
  const resolvedDescription = (library?.description ?? cachedLibrary?.description ?? '').trim()
  const descriptionToShow = resolvedDescription || t('libraries.list.description.empty')
  const displayName = resolvedName || t('bookshelves.library.loadingName')

  return (
    <main className={styles.page} style={libraryThemeVars}>
      <div className={styles.container}>
      {libraryError && (
        <div className={styles.errorBanner}>
          <div>
            <strong>{t('bookshelves.library.error.loadFailed')}：</strong>
            {(libraryError as any)?.response?.status ? `HTTP ${(libraryError as any)?.response?.status}` : ''}
            {(libraryError as any)?.message ? ` · ${(libraryError as any)?.message}` : ''}
          </div>
          <Button size="sm" variant="secondary" onClick={() => refetchLibrary()}>
            {t('button.retry')}
          </Button>
        </div>
      )}

      <Breadcrumb
        items={[
          { label: t('bookshelves.library.breadcrumb.list'), href: '/admin/libraries' },
          { label: displayName, active: true },
        ]}
      />

      <header className={styles.header}>
        <div className={styles.titleBlock}>
          <h1>{displayName}</h1>
          <p className={styles.description} data-empty={resolvedDescription ? undefined : 'true'}>
            {descriptionToShow}
          </p>
          {isLibraryLoading && library === undefined && cachedLibrary && (
            <span className={styles.loadingHint}>{t('bookshelves.library.loadingHint')}</span>
          )}
        </div>
      </header>

      <section className={styles.summarySection}>
        <div className={styles.summaryCard}>
          <span className={styles.summaryValue}>{snapshot.total}</span>
          <span className={styles.summaryLabel}>{t('bookshelves.library.summary.total')}</span>
        </div>
        {summaryBadges.map((badge) => (
          <div key={badge.label} className={styles.summaryBadge}>
            <span className={styles.badgeValue}>{badge.value}</span>
            <span className={styles.badgeLabel}>{badge.label}</span>
          </div>
        ))}
      </section>

      {showProgress && (
        <div className={styles.progressNotice}>
          <div className={styles.progressTrack} aria-hidden="true">
            <div className={styles.progressValue} style={{ width: `${progressPercentage}%` }} />
          </div>
          <span className={styles.progressLabel}>{limitMessage}</span>
        </div>
      )}

      <BookshelfDashboardBoard
        libraryId={libraryId}
        sort={sort}
        statusFilter={statusFilter}
        fallbackThemeColor={libraryTheme.hex}
        libraryTags={library?.tags || cachedLibrary?.tags}
        libraryName={library?.name || cachedLibrary?.name || ''}
        onSortChange={setSort}
        onStatusFilterChange={setStatusFilter}
        onSnapshotChange={handleSnapshotChange}
        onOpenBookshelf={handleOpenBookshelf}
        onCreateBookshelf={handleCreateBookshelf}
      />
      <LibraryForm
        isOpen={isCreateDialogOpen}
        mode="create"
        onClose={handleCreateDialogClose}
        onSubmit={handleCreateDialogSubmit}
        isLoading={isCreateDialogLoading}
        isTagPrefillLoading={false}
        maxTags={TAG_LIMIT}
        createTitle={t('bookshelves.library.form.title')}
        createSubtitle={t('bookshelves.library.form.subtitle')}
        nameLabel={t('bookshelves.library.form.nameLabel')}
        namePlaceholder={t('bookshelves.library.form.namePlaceholder')}
        descriptionLabel={t('bookshelves.library.form.descriptionLabel')}
        descriptionPlaceholder={t('bookshelves.library.form.descriptionPlaceholder')}
        createSubmitLabel={t('bookshelves.library.form.submitLabel')}
        showThemeColorField={false}
      />
      </div>
    </main>
  )
}
