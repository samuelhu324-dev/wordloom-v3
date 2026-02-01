import { sendQuickLogEvent } from './quickLogClient';
import { createCorrelationId, nowMs } from './correlationId';

export type ImageLoadHandle = {
  correlationId: string;
  operation: string;
  originalUrl: string;
  instrumentedUrl: string;
  tStartMs: number;
};

const shouldAttachCidToUrl = (url: string): boolean => {
  // blob/data URLs never hit backend.
  if (url.startsWith('blob:') || url.startsWith('data:')) {
    return false;
  }
  return true;
};

export const appendQueryParam = (url: string, key: string, value: string): string => {
  try {
    // Support absolute and relative URLs.
    const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
    const u = new URL(url, base);
    u.searchParams.set(key, value);

    // If input was relative, return relative (pathname + search + hash)
    const isAbsoluteInput = /^https?:\/\//i.test(url);
    return isAbsoluteInput ? u.toString() : `${u.pathname}${u.search}${u.hash}`;
  } catch {
    const sep = url.includes('?') ? '&' : '?';
    return `${url}${sep}${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
  }
};

const pickLatestResourceEntry = (name: string): PerformanceResourceTiming | undefined => {
  if (typeof performance === 'undefined' || typeof performance.getEntriesByName !== 'function') {
    return undefined;
  }
  try {
    const entries = performance.getEntriesByName(name).filter((e) => e.entryType === 'resource') as PerformanceResourceTiming[];
    if (!entries.length) return undefined;
    return entries[entries.length - 1];
  } catch {
    return undefined;
  }
};

export const startImageLoad = (
  operation: string,
  url: string,
  correlationId?: string,
): ImageLoadHandle => {
  const cid = correlationId || createCorrelationId();
  const instrumentedUrl = shouldAttachCidToUrl(url) ? appendQueryParam(url, 'cid', cid) : url;
  return {
    correlationId: cid,
    operation,
    originalUrl: url,
    instrumentedUrl,
    tStartMs: nowMs(),
  };
};

export const reportImageLoaded = (
  handle: ImageLoadHandle,
  img: HTMLImageElement,
  extra?: Record<string, unknown>,
) => {
  const tEndMs = nowMs();
  const durationMs = tEndMs - handle.tStartMs;

  const perf = pickLatestResourceEntry(handle.instrumentedUrl);

  sendQuickLogEvent({
    type: 'ui.image.loaded',
    timestamp: Date.now(),
    data: {
      correlation_id: handle.correlationId,
      operation: handle.operation,
      url: handle.instrumentedUrl,
      url_original: handle.originalUrl,
      duration_ms: durationMs,
      natural_width: img.naturalWidth,
      natural_height: img.naturalHeight,
      transfer_size: perf?.transferSize,
      encoded_body_size: perf?.encodedBodySize,
      decoded_body_size: perf?.decodedBodySize,
      resource_duration_ms: perf?.duration,
      resource_start_time_ms: perf?.startTime,
      ...extra,
    },
  });
};

export const reportImageError = (
  handle: ImageLoadHandle,
  extra?: Record<string, unknown>,
) => {
  const tEndMs = nowMs();
  const durationMs = tEndMs - handle.tStartMs;

  sendQuickLogEvent({
    type: 'ui.image.error',
    timestamp: Date.now(),
    data: {
      correlation_id: handle.correlationId,
      operation: handle.operation,
      url: handle.instrumentedUrl,
      url_original: handle.originalUrl,
      duration_ms: durationMs,
      ...extra,
    },
  });
};
