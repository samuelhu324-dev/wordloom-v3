import { useCallback, useEffect, useMemo, useState } from 'react';
import type { BookMaturity } from '@/entities/book';

export type BookFilterScope = 'local' | 'global';
export type BookMaturityOrderPreset = 'seed-first' | 'legacy-first';

const MATURITY_ORDER_PRESET_MAP: Record<BookMaturityOrderPreset, BookMaturity[]> = {
  'seed-first': ['seed', 'growing', 'stable', 'legacy'],
  'legacy-first': ['legacy', 'stable', 'growing', 'seed'],
};

const STORAGE_KEY = 'wl.bookList.filters';

export interface BookFilterState {
  stageVisibility: Record<BookMaturity, boolean>;
  orderPreset: BookMaturityOrderPreset;
  pinnedFirst: boolean;
  searchScope: BookFilterScope;
  searchText: string;
  combinedView: boolean;
}

const DEFAULT_STATE: BookFilterState = {
  stageVisibility: {
    seed: true,
    growing: true,
    stable: true,
    legacy: true,
  },
  orderPreset: 'seed-first',
  pinnedFirst: true,
  searchScope: 'local',
  searchText: '',
  combinedView: false,
};

const normalizeOrderPreset = (value: string | undefined): BookMaturityOrderPreset => {
  if (value === 'legacy-first') return 'legacy-first';
  return 'seed-first';
};

const safeParseState = (raw: string | null): BookFilterState => {
  if (!raw) return DEFAULT_STATE;
  try {
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_STATE,
      ...parsed,
      stageVisibility: {
        ...DEFAULT_STATE.stageVisibility,
        ...(parsed?.stageVisibility ?? {}),
      },
      orderPreset: normalizeOrderPreset(parsed?.orderPreset),
      combinedView: Boolean(parsed?.combinedView),
    } satisfies BookFilterState;
  } catch {
    return DEFAULT_STATE;
  }
};

export const getOrderForPreset = (preset: BookMaturityOrderPreset): BookMaturity[] => MATURITY_ORDER_PRESET_MAP[preset] ?? MATURITY_ORDER_PRESET_MAP['seed-first'];

interface UseBookFiltersResult {
  state: BookFilterState;
  toggleStage: (stage: BookMaturity) => void;
  enableAllStages: () => void;
  setOrderPreset: (preset: BookMaturityOrderPreset) => void;
  setPinnedFirst: (value: boolean) => void;
  setSearchScope: (scope: BookFilterScope) => void;
  setSearchText: (value: string) => void;
  clearSearch: () => void;
  setCombinedView: (value: boolean) => void;
  toggleCombinedView: () => void;
  reset: () => void;
}

export const useBookFilters = (): UseBookFiltersResult => {
  const [state, setState] = useState<BookFilterState>(() => {
    if (typeof window === 'undefined') return DEFAULT_STATE;
    return safeParseState(window.localStorage.getItem(STORAGE_KEY));
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const toggleStage = useCallback((stage: BookMaturity) => {
    setState((prev) => ({
      ...prev,
      stageVisibility: {
        ...prev.stageVisibility,
        [stage]: !prev.stageVisibility[stage],
      },
    }));
  }, []);

  const enableAllStages = useCallback(() => {
    setState((prev) => ({
      ...prev,
      stageVisibility: {
        seed: true,
        growing: true,
        stable: true,
        legacy: true,
      },
    }));
  }, []);

  const setOrderPreset = useCallback((preset: BookMaturityOrderPreset) => {
    setState((prev) => ({ ...prev, orderPreset: preset }));
  }, []);

  const setPinnedFirst = useCallback((value: boolean) => {
    setState((prev) => ({ ...prev, pinnedFirst: value }));
  }, []);

  const setSearchScope = useCallback((scope: BookFilterScope) => {
    setState((prev) => ({ ...prev, searchScope: scope }));
  }, []);

  const setSearchText = useCallback((value: string) => {
    setState((prev) => ({ ...prev, searchText: value }));
  }, []);

  const clearSearch = useCallback(() => {
    setState((prev) => ({ ...prev, searchText: '' }));
  }, []);

  const setCombinedView = useCallback((value: boolean) => {
    setState((prev) => ({ ...prev, combinedView: value }));
  }, []);

  const toggleCombinedView = useCallback(() => {
    setState((prev) => ({ ...prev, combinedView: !prev.combinedView }));
  }, []);

  const reset = useCallback(() => {
    setState(DEFAULT_STATE);
  }, []);

  return useMemo(
    () => ({
      state,
      toggleStage,
      enableAllStages,
      setOrderPreset,
      setPinnedFirst,
      setSearchScope,
      setSearchText,
      clearSearch,
      setCombinedView,
      toggleCombinedView,
      reset,
    }),
    [state, toggleStage, enableAllStages, setOrderPreset, setPinnedFirst, setSearchScope, setSearchText, clearSearch, setCombinedView, toggleCombinedView, reset],
  );
};
