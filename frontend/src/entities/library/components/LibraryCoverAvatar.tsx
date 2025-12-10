import React, { useMemo } from 'react';
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
  const initial = useMemo(() => {
    const trimmed = name.trim();
    if (!trimmed) return 'L';
    return trimmed.charAt(0).toUpperCase();
  }, [name]);

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
      {coverUrl ? (
        <img
          src={coverUrl}
          alt={`${name} cover`}
          loading="lazy"
          decoding="async"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        <span style={{ lineHeight: 1 }}>{initial}</span>
      )}
    </div>
  );
};
