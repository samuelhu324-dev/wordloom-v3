import type { BookCoverIconId, BookMaturity } from '@/entities/book';
import { generateCoverPlaceholder } from '@/shared/ui/coverPlaceholder';
import {
  DEFAULT_COVER_COLOR,
  FALLBACK_LUCIDE_ICON,
  STAGE_VISUALS,
  TAG_ICON_MAP,
  type BookStage,
} from './theme.config';

export type BookThemeIconType = 'lucide' | 'image';

export interface BookThemeInput {
  id?: string;
  title?: string;
  stage?: BookStage;
  legacyFlag?: boolean;
  coverIconId?: BookCoverIconId | null;
  coverColor?: string | null;
  coverImageUrl?: string | null;
  libraryColorSeed?: string | null;
}

export interface BookThemeResult {
  accentColor: string;
  glyph: string;
  iconType: BookThemeIconType;
  iconId: BookCoverIconId | null;
  iconSource?: string;
}

const isHexColor = (value?: string | null): value is string => {
  if (!value) return false;
  return /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value.trim());
};

const normalizeHex = (value: string): string => {
  const hex = value.trim();
  if (hex.length === 4) {
    return `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`.toLowerCase();
  }
  return hex.toLowerCase();
};

export const getStageVisual = (stage: BookStage | undefined): { color: string; icon: string } => {
  if (!stage) {
    return STAGE_VISUALS.seed;
  }
  return STAGE_VISUALS[stage as BookStage] ?? STAGE_VISUALS.seed;
};

export const getCoverColor = (params: { explicitColor?: string | null; title?: string; id?: string; librarySeed?: string | null }) => {
  if (isHexColor(params.explicitColor)) {
    const glyph = deriveGlyph(params.title);
    return { color: normalizeHex(params.explicitColor!), glyph };
  }

  const placeholderSeed = params.librarySeed ? { seed: params.librarySeed } : params.id;
  const placeholder = generateCoverPlaceholder(params.title || 'Book', placeholderSeed);
  return {
    color: placeholder.bgColor || DEFAULT_COVER_COLOR,
    glyph: placeholder.glyph,
  };
};

export const getBookTheme = (input: BookThemeInput): BookThemeResult => {
  const { color, glyph } = getCoverColor({
    explicitColor: input.coverColor,
    title: input.title,
    id: input.id,
    librarySeed: input.libraryColorSeed,
  });

  if (input.coverImageUrl) {
    return {
      accentColor: color,
      glyph,
      iconType: 'image',
      iconId: null,
      iconSource: input.coverImageUrl,
    };
  }

  const iconId: BookCoverIconId | null = input.coverIconId ?? null;

  return {
    accentColor: color,
    glyph,
    iconType: 'lucide',
    iconId,
  };
};

export const mapLucideIconFromTag = (tag?: string): string => {
  if (!tag) return FALLBACK_LUCIDE_ICON;
  const normalized = tag.trim().toLowerCase();
  return TAG_ICON_MAP[normalized] ?? FALLBACK_LUCIDE_ICON;
};

export const shouldAllowCustomIcon = (maturity: BookMaturity, legacyFlag: boolean): boolean =>
  maturity === 'stable' && !legacyFlag;

const deriveGlyph = (title?: string): string => {
  if (!title) return 'B';
  const trimmed = title.trim();
  if (!trimmed) return 'B';
  const firstChar = trimmed[0];
  if (/^[a-zA-Z]$/.test(firstChar)) {
    return firstChar.toUpperCase();
  }
  return firstChar;
};
