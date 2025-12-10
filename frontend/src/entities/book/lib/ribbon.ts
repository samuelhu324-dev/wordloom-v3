import { BookMaturity } from '../types';

const MATURITY_LABEL_MAP: Record<BookMaturity, string> = {
  seed: 'SEED',
  growing: 'GROWING',
  stable: 'STABLE',
  legacy: 'LEGACY',
};

const LETTER_MATCHER = /[A-Za-z]/;

export interface BookRibbonResult {
  label: string;
  fromTag: boolean;
}

const normalizeTagLabel = (tagName?: string | null, maxLength: number = 7): string => {
  if (!tagName) {
    return '';
  }
  const letters: string[] = [];
  for (const char of tagName) {
    if (LETTER_MATCHER.test(char)) {
      letters.push(char.toUpperCase());
      if (letters.length >= maxLength) {
        break;
      }
    }
  }
  return letters.join('');
};

export const buildBookRibbon = (
  tagNames?: string[] | null,
  maturity: BookMaturity = 'seed',
  options: { maxLength?: number } = {},
): BookRibbonResult => {
  const { maxLength = 7 } = options;
  const primaryTag = Array.isArray(tagNames) ? tagNames[0] : undefined;
  const tagLabel = normalizeTagLabel(primaryTag, maxLength);

  if (tagLabel.length > 0) {
    return {
      label: tagLabel,
      fromTag: true,
    };
  }

  const fallback = MATURITY_LABEL_MAP[maturity] ?? MATURITY_LABEL_MAP.seed;
  return {
    label: fallback,
    fromTag: false,
  };
};

export const MATURITY_RIBBON_LABELS = MATURITY_LABEL_MAP;
