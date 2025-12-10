import { api } from '@/shared/api/client';
import { listBookshelves } from '@/features/bookshelf/model/api';
import type { BookshelfDto } from '@/entities/bookshelf';
import type {
  BasementBookshelfOption,
  BasementGroupDto,
  BasementGroupsResponseDto,
  DeletedBookDto,
} from '@/entities/basement/types';

interface BasementBookResponseDto {
  id: string;
  library_id: string;
  bookshelf_id: string;
  previous_bookshelf_id?: string | null;
  title: string;
  summary?: string | null;
  status: string;
  block_count: number;
  moved_to_basement_at?: string | null;
  soft_deleted_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

interface BasementBookListResponseDto {
  items: BasementBookResponseDto[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface FetchBasementGroupsParams {
  libraryId: string;
  skip?: number;
  limit?: number;
}

const UNKNOWN_KEY_PREFIX = '__unknown__';
const BOOKSHELF_PAGE_SIZE = 100; // backend limit per query (see bookshelves router Query limit<=100)

export async function fetchBasementGroups(
  params: FetchBasementGroupsParams
): Promise<BasementGroupsResponseDto> {
  const { libraryId, skip = 0, limit = 40 } = params;
  if (!libraryId) {
    throw new Error('libraryId is required to query Basement data');
  }

  const [{ data }, shelvesPage] = await Promise.all([
    api.get<BasementBookListResponseDto>(`/admin/libraries/${libraryId}/basement/books`, {
      params: { skip, limit },
    }),
    listBookshelves({ libraryId, page: 1, pageSize: BOOKSHELF_PAGE_SIZE }),
  ]);

  const shelvesMap = new Map<string, BookshelfDto>();
  shelvesPage.items.forEach((shelf) => shelvesMap.set(shelf.id, shelf));

  const availableBookshelves: BasementBookshelfOption[] = shelvesPage.items
    .filter((shelf) => shelf.type !== 'BASEMENT')
    .map((shelf) => ({
      id: shelf.id,
      name: shelf.name,
      isBasement: shelf.type === 'BASEMENT',
      exists: true,
    }));

  const groupsMap = new Map<string, BasementGroupDto>();
  let unknownCounter = 0;
  let latestDeletedAt: string | undefined;

  for (const item of data.items) {
    const deletedAt = item.soft_deleted_at || item.moved_to_basement_at || item.updated_at || item.created_at || '';
    if (!latestDeletedAt || (deletedAt && deletedAt > latestDeletedAt)) {
      latestDeletedAt = deletedAt;
    }

    const originalShelfId = item.previous_bookshelf_id || null;
    const groupKey = originalShelfId ?? `${UNKNOWN_KEY_PREFIX}:${libraryId}`;
    const bookshelfMeta = describeOriginalBookshelf(originalShelfId, shelvesMap, () => ++unknownCounter);

    if (!groupsMap.has(groupKey)) {
      groupsMap.set(groupKey, {
        bookshelf_id: originalShelfId ?? groupKey,
        name: bookshelfMeta.name,
        bookshelf_exists: bookshelfMeta.exists,
        count: 0,
        latest_deleted_at: deletedAt,
        items: [],
      });
    }

    const group = groupsMap.get(groupKey)!;
    group.count += 1;
    if (!group.latest_deleted_at || deletedAt > group.latest_deleted_at) {
      group.latest_deleted_at = deletedAt;
    }

    const book: DeletedBookDto = {
      book_id: item.id,
      title: item.title,
      summary: item.summary,
      deleted_at: deletedAt,
      original_bookshelf_id: originalShelfId,
      original_bookshelf_name: bookshelfMeta.name,
      previous_bookshelf_id: originalShelfId,
      basement_bookshelf_id: item.bookshelf_id,
      library_id: item.library_id,
      status: item.status,
      block_count: item.block_count,
    };

    group.items.push(book);
  }

  const groups = Array.from(groupsMap.values()).sort((a, b) => {
    const left = a.latest_deleted_at ?? '';
    const right = b.latest_deleted_at ?? '';
    return right.localeCompare(left);
  });

  return {
    items: groups,
    total: data.total,
    availableBookshelves,
    stats: {
      bookTotal: data.total,
      groupTotal: groups.length,
      lostShelves: groups.filter((group) => !group.bookshelf_exists).length,
      latestDeletedAt,
    },
    fetchedAt: new Date().toISOString(),
  };
}

export interface RestoreBookPayload {
  target_bookshelf_id?: string | null;
}

export async function restoreBook(
  bookId: string,
  payload: RestoreBookPayload
): Promise<{ book_id: string; restored_to: string }> {
  const { data } = await api.post<{ book_id: string; restored_to: string }>(
    `/admin/books/${bookId}/restore-from-basement`,
    {
      target_bookshelf_id: payload.target_bookshelf_id || undefined,
    }
  );
  return data;
}

export async function hardDeleteBook(bookId: string): Promise<void> {
  await api.delete(`/admin/books/${bookId}`);
}

export async function fetchBasementStats(): Promise<{ deleted_books: number; deleted_bookshelves: number }> {
  return { deleted_books: 0, deleted_bookshelves: 0 };
}

function describeOriginalBookshelf(
  bookshelfId: string | null,
  shelvesMap: Map<string, BookshelfDto>,
  nextUnknownIndex: () => number
): { name: string; exists: boolean } {
  if (bookshelfId) {
    const shelf = shelvesMap.get(bookshelfId);
    if (shelf) {
      return { name: shelf.name, exists: shelf.type !== 'BASEMENT' };
    }
    return { name: `已删除书架 ${bookshelfId.slice(0, 6)}`, exists: false };
  }

  const idx = nextUnknownIndex();
  return { name: `未标记书架 #${idx}`, exists: false };
}
