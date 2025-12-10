// Basement entity & virtual library DTO definitions
// NOTE: VirtualBasementLibraryDto does not correspond to a real backend aggregate.
// Mapping layer inserts this card locally after fetching real libraries.

export interface VirtualBasementLibraryDto {
  id: '__BASEMENT__';
  name: string; // 'Basement' (i18n ready)
  locked: true;
  stats: {
    deleted_books: number;
    deleted_bookshelves: number;
  };
}

export interface DeletedBookDto {
  book_id: string;
  title: string;
  deleted_at: string;
  summary?: string | null;
  original_bookshelf_id: string | null;
  original_bookshelf_name?: string;
  previous_bookshelf_id?: string | null; // alias kept for clarity when mapping backend payloads
  basement_bookshelf_id?: string | null;
  library_id?: string;
  status?: string;
  block_count?: number;
  author?: string;
  tag_ids?: string[];
}

export interface BasementGroupDto {
  bookshelf_id: string;
  name: string;
  bookshelf_exists: boolean;
  count: number; // items length
  latest_deleted_at?: string;
  items: DeletedBookDto[];
}

export interface BasementBookshelfOption {
  id: string;
  name: string;
  isBasement?: boolean;
  exists?: boolean;
}

export interface BasementGroupsStats {
  bookTotal: number;
  groupTotal: number;
  lostShelves: number;
  latestDeletedAt?: string;
}

export interface BasementGroupsResponseDto {
  items: BasementGroupDto[];
  total: number; // total deleted books across groups
  message?: string;
  availableBookshelves?: BasementBookshelfOption[];
  stats?: BasementGroupsStats;
  fetchedAt?: string;
}

export function createVirtualBasementLibrary(stats?: Partial<VirtualBasementLibraryDto['stats']>): VirtualBasementLibraryDto {
  return {
    id: '__BASEMENT__',
    name: 'Basement',
    locked: true,
    stats: {
      deleted_books: stats?.deleted_books ?? 0,
      deleted_bookshelves: stats?.deleted_bookshelves ?? 0,
    },
  };
}
