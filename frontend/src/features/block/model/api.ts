import { apiClient } from '@/shared/api';
import {
  BlockApiResponse,
  BlockDto,
  BlockTypeApi,
  CreateBlockRequest,
  UpdateBlockRequest,
  mapApiTypeToKind,
  mapKindToApiType,
  parseBlockContent,
} from '@/entities/block';

// Phase0 新分页端点基于后端 /api/v1/phase0/books/{book_id}/blocks
// 返回结构: { items, total, page, page_size, has_more }
// 旧的 /blocks 列表继续保留兼容（不分页或后续改造）。

const MAX_BLOCK_PAGE_SIZE = 100;
const DEFAULT_BLOCK_PAGE_SIZE = 50;

/** List all blocks, optionally filtered by book_id */
const normalizeBlock = (raw: BlockApiResponse): BlockDto => {
  const apiType = raw.type ?? raw.block_type;
  const kind = apiType ? mapApiTypeToKind(apiType) : 'custom';
  return {
    ...raw,
    kind,
    content: parseBlockContent(kind, raw.content),
    fractional_index: raw.fractional_index ?? raw.order ?? '0',
  };
};

const normalizeList = (items?: BlockApiResponse[]): BlockDto[] =>
  Array.isArray(items) ? items.map(normalizeBlock) : [];

interface FetchBlocksPageParams {
  bookId: string;
  skip: number;
  limit: number;
  includeDeleted?: boolean;
}

const clampPageSize = (value?: number) => {
  if (!value || Number.isNaN(value)) {
    return DEFAULT_BLOCK_PAGE_SIZE;
  }
  return Math.min(Math.max(1, value), MAX_BLOCK_PAGE_SIZE);
};

const fetchBlocksPage = async ({
  bookId,
  skip,
  limit,
  includeDeleted,
}: FetchBlocksPageParams) => {
  const params = new URLSearchParams({
    book_id: bookId,
    skip: String(skip),
    limit: String(limit),
  });
  if (includeDeleted) {
    params.set('include_deleted', 'true');
  }
  const response = await apiClient.get<{ total: number; items: BlockApiResponse[] }>(
    `/blocks?${params.toString()}`
  );

  return {
    items: normalizeList(response.data?.items),
    total: response.data?.total ?? 0,
  };
};

export const listBlocks = async (
  bookId?: string,
  options?: { pageSize?: number; includeDeleted?: boolean }
): Promise<BlockDto[]> => {
  if (!bookId) {
    const response = await apiClient.get<{ total: number; items: BlockApiResponse[] }>(`/blocks`);
    return normalizeList(response.data?.items);
  }

  const limit = clampPageSize(options?.pageSize);
  const includeDeleted = Boolean(options?.includeDeleted);
  const aggregated: BlockDto[] = [];
  let skip = 0;
  let expectedTotal: number | null = null;
  const SAFETY_PAGE_CAP = 50;

  for (let pageIndex = 0; pageIndex < SAFETY_PAGE_CAP; pageIndex += 1) {
    const { items, total } = await fetchBlocksPage({
      bookId,
      skip,
      limit,
      includeDeleted,
    });

    aggregated.push(...items);
    if (expectedTotal === null && total > 0) {
      expectedTotal = total;
    }

    if (items.length < limit) {
      break;
    }

    skip += limit;

    if (expectedTotal !== null && aggregated.length >= expectedTotal) {
      break;
    }
  }

  return aggregated;
};

export interface PaginatedBlocksResult {
  items: BlockDto[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export const listBlocksPaginatedPhase0 = async (
  bookId: string,
  page: number,
  pageSize: number
): Promise<PaginatedBlocksResult> => {
  const response = await apiClient.get<{
    items: BlockApiResponse[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
  }>(`/phase0/books/${bookId}/blocks?page=${page}&page_size=${pageSize}`);

  return {
    ...response.data,
    items: normalizeList(response.data?.items),
  };
};

/** Get single block by ID */
export const getBlock = async (blockId: string): Promise<BlockDto> => {
  const response = await apiClient.get<BlockApiResponse>(
    `/blocks/${blockId}`
  );
  return normalizeBlock(response.data);
};

/** Create block (request must include book_id) */
export const createBlock = async (request: CreateBlockRequest): Promise<BlockDto> => {
  const payload = {
    type: mapKindToApiType(request.kind),
    content: request.content ?? '',
    heading_level: request.heading_level,
  } satisfies {
    type: BlockTypeApi;
    content: string;
    heading_level?: number | null;
  };

  const response = await apiClient.post<BlockApiResponse>(
    `/phase0/books/${request.book_id}/blocks`,
    payload
  );
  return normalizeBlock(response.data);
};

/** Update block */
export const updateBlock = async (
  blockId: string,
  request: UpdateBlockRequest
): Promise<BlockDto> => {
  const payload: { content?: string; type?: BlockTypeApi } = {
    content: request.content,
  };
  if (request.kind) {
    payload.type = mapKindToApiType(request.kind);
  }
  const response = await apiClient.patch<BlockApiResponse>(
    `/phase0/blocks/${blockId}`,
    payload
  );
  return normalizeBlock(response.data);
};

/** Delete block */
export const deleteBlock = async (blockId: string): Promise<void> => {
  await apiClient.delete(`/phase0/blocks/${blockId}`);
};

export const restoreBlock = async (blockId: string): Promise<BlockDto> => {
  const response = await apiClient.post<BlockApiResponse>(`/phase0/blocks/${blockId}/restore`);
  return normalizeBlock(response.data);
};

export interface DeletedBlocksResponse {
  items: BlockDto[];
  total: number;
}

export const listDeletedBlocks = async (bookId: string, skip=0, limit=50): Promise<DeletedBlocksResponse> => {
  const resp = await apiClient.get<{ items: BlockApiResponse[]; total: number }>(`/blocks/deleted?book_id=${bookId}&skip=${skip}&limit=${limit}`);
  return {
    total: resp.data?.total ?? 0,
    items: normalizeList(resp.data?.items),
  };
};

export const reorderBlock = async (blockId: string, newOrder: string): Promise<BlockDto> => {
  const resp = await apiClient.post<BlockApiResponse>(`/blocks/reorder`, { block_id: blockId, new_order: newOrder });
  return normalizeBlock(resp.data);
};
