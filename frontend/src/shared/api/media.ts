import { buildApiUrl } from './client';

/**
 * 构建媒体文件下载地址，自动附加 cache bust 参数避免浏览器缓存陈旧封面。
 */
export const buildMediaFileUrl = (mediaId: string, cacheKey?: string | number | null): string => {
  if (!mediaId) {
    throw new Error('mediaId is required to build media file url');
  }
  const baseUrl = buildApiUrl(`/media/${mediaId}/file`);
  if (cacheKey === undefined || cacheKey === null || cacheKey === '') {
    return baseUrl;
  }
  const separator = baseUrl.includes('?') ? '&' : '?';
  return `${baseUrl}${separator}v=${encodeURIComponent(String(cacheKey))}`;
};
