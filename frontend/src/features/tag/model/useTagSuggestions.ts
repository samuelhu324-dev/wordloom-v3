import type { TagDto } from '@/entities/tag';
import { useDebouncedValue } from '@/shared/lib/hooks/useDebouncedValue';
import { TAG_SUGGESTION_LIMIT } from '../constants';
import { useMostUsedTags, useTagSearch } from './hooks';
import { useI18n } from '@/i18n/useI18n';

export interface TagSuggestionResult {
  items: TagDto[];
  label: string;
  isLoading: boolean;
  isSearching: boolean;
  query: string;
}

interface UseTagSuggestionsOptions {
  isOpen?: boolean;
  enabled?: boolean;
  debounceMs?: number;
}

export const useTagSuggestions = (
  value: string,
  { isOpen = true, enabled = true, debounceMs = 250 }: UseTagSuggestionsOptions = {},
): TagSuggestionResult => {
  const { t } = useI18n();
  const debouncedQuery = useDebouncedValue(value.trim(), debounceMs);
  const isSearching = debouncedQuery.length > 0;
  const shouldQuery = enabled && isOpen;

  const { data: searchResults = [], isFetching: searchLoading } = useTagSearch(debouncedQuery, {
    limit: TAG_SUGGESTION_LIMIT,
    enabled: shouldQuery && isSearching,
  });

  const { data: popularTags = [], isFetching: popularLoading } = useMostUsedTags({
    limit: TAG_SUGGESTION_LIMIT,
    enabled: shouldQuery && !isSearching,
  });

  const items = (isSearching ? searchResults : popularTags) ?? [];
  const isLoading = isSearching ? searchLoading : popularLoading;

  return {
    items,
    label: isSearching ? t('tags.suggestions.matchLabel') : t('tags.suggestions.commonLabel'),
    isLoading,
    isSearching,
    query: debouncedQuery,
  };
};
