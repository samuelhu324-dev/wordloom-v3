import React, { useEffect, useMemo, useState } from 'react';
import { DEFAULT_LIBRARY_SILVER_GRADIENT } from '../utils/coverGradient';

export interface LibraryCoverAvatarProps {
  coverUrl?: string | null;
  libraryId: string;
  name: string;
  size?: number | string;
}

export const LibraryCoverAvatar: React.FC<LibraryCoverAvatarProps> = ({
  coverUrl,
  libraryId,
  name,
  size = 'var(--library-avatar-size)',
}) => {
  const resolvedSize = typeof size === 'number' ? `${size}px` : size;
  const gradient = DEFAULT_LIBRARY_SILVER_GRADIENT;
  const [resolvedCover, setResolvedCover] = useState<string | null>(coverUrl ?? null);
  const initial = useMemo(() => {
    const trimmed = name.trim();
    if (!trimmed) return 'L';
    return trimmed.charAt(0).toUpperCase();
  }, [name]);

  useEffect(() => {
    setResolvedCover(coverUrl ?? null);
  }, [coverUrl]);

  const showImage = Boolean(resolvedCover);

  return (
    <div
      aria-label={`库封面 ${name}`}
      style={{
        width: resolvedSize,
        height: resolvedSize,
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        flexShrink: 0,
        background: gradient,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'rgba(255, 255, 255, 0.9)',
        fontSize: '0.75rem',
        fontWeight: 600,
        textTransform: 'uppercase',
      }}
    >
      {showImage ? (
        <img
          src={resolvedCover ?? undefined}
          alt={`${name} cover`}
          loading="lazy"
          decoding="async"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          onError={() => setResolvedCover(null)}
        />
      ) : (
        <span style={{ lineHeight: 1 }}>{initial}</span>
      )}
    </div>
  );
};
