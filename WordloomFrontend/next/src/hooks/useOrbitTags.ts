/**
 * useOrbitTags - 获取 Orbit 系统的所有标签
 */
'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

export interface Tag {
  id: string;
  name: string;
  color: string;
  icon?: string;
  description?: string;
}

/**
 * 获取所有标签
 */
export function useOrbitTags() {
  const { data: tags = [], isLoading, error } = useQuery({
    queryKey: ['orbit', 'tags'],
    queryFn: async () => {
      const response = await fetch('/api/orbit/tags');
      if (!response.ok) throw new Error('Failed to fetch tags');
      return response.json();
    },
  });

  return {
    tags: tags as Tag[],
    isLoading,
    error: error as Error | null,
  };
}

/**
 * 获取所有标签的映射（id -> Tag）
 */
export function useTagMap() {
  const { tags } = useOrbitTags();
  const tagMap = new Map<string, Tag>();

  tags.forEach((tag) => {
    tagMap.set(tag.id, tag);
  });

  return tagMap;
}

/**
 * 根据 ID 列表获取标签
 */
export function useTagsByIds(tagIds: string[]) {
  const tagMap = useTagMap();
  return tagIds
    .map((id) => tagMap.get(id))
    .filter((tag): tag is Tag => !!tag);
}
