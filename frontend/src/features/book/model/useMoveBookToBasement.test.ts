import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@tanstack/react-query', () => ({
  useMutation: vi.fn(),
  useQueryClient: vi.fn(),
}));

vi.mock('./api', () => ({
  moveBookToBasement: vi.fn(),
}));

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { moveBookToBasement } from './api';
import { useMoveBookToBasement } from './hooks';

type MutationConfig = {
  mutationFn: (variables: { bookId: string; basementBookshelfId: string }) => Promise<unknown> | unknown;
  onSuccess?: (...args: any[]) => unknown;
  onSettled?: (...args: any[]) => unknown;
};

describe('useMoveBookToBasement', () => {
  const mutationResult = { mutate: vi.fn(), mutateAsync: vi.fn() };
  const useMutationMock = vi.mocked(useMutation);
  const useQueryClientMock = vi.mocked(useQueryClient);
  const moveBookToBasementMock = vi.mocked(moveBookToBasement);

  let invalidateQueriesMock: ReturnType<typeof vi.fn>;
  let capturedConfig: MutationConfig | undefined;

  beforeEach(() => {
    vi.clearAllMocks();
    invalidateQueriesMock = vi.fn();
    capturedConfig = undefined;

    useQueryClientMock.mockReturnValue({
      invalidateQueries: invalidateQueriesMock,
    } as any);

    useMutationMock.mockImplementation((config: MutationConfig) => {
      capturedConfig = config;
      return mutationResult as any;
    });

    moveBookToBasementMock.mockResolvedValue();
  });

  it('calls backend API and invalidates caches on success', async () => {
    const result = useMoveBookToBasement();

    expect(result).toBe(mutationResult);
    expect(capturedConfig).toBeDefined();

    const payload = { bookId: 'book-123', basementBookshelfId: 'shelf-basement' };
    await capturedConfig!.mutationFn(payload);
    expect(moveBookToBasementMock).toHaveBeenCalledWith(payload);

    invalidateQueriesMock.mockClear();
    await capturedConfig!.onSuccess?.(undefined as any, undefined as any, undefined as any);
    await capturedConfig!.onSettled?.(undefined, undefined, undefined);

    expect(invalidateQueriesMock).toHaveBeenNthCalledWith(1, { queryKey: ['books'] });
    expect(invalidateQueriesMock).toHaveBeenNthCalledWith(2, { queryKey: ['basement'] });
    expect(invalidateQueriesMock).toHaveBeenNthCalledWith(3, { queryKey: ['bookshelves', 'dashboard'] });
  });

  it('still invalidates basement caches when the mutation errors', async () => {
    useMoveBookToBasement();
    expect(capturedConfig).toBeDefined();

    await capturedConfig!.onSettled?.(undefined, new Error('network'), undefined);

    expect(invalidateQueriesMock).toHaveBeenNthCalledWith(1, { queryKey: ['basement'] });
    expect(invalidateQueriesMock).toHaveBeenNthCalledWith(2, { queryKey: ['bookshelves', 'dashboard'] });
  });
});
