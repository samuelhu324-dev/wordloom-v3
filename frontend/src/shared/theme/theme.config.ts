export type BookStage = 'seed' | 'growing' | 'stable' | 'legacy';

export type StageVisualConfig = {
  color: string;
  icon: string;
};

export const DEFAULT_COVER_COLOR = '#1d1f50';
export const FALLBACK_LUCIDE_ICON = 'book-open';
export const STABLE_DEFAULT_ICON = 'award';

export const STAGE_VISUALS: Record<BookStage, StageVisualConfig> = {
  seed: { color: '#6b7280', icon: 'sprout' },
  growing: { color: '#3a85ff', icon: 'leaf' },
  stable: { color: '#2da44e', icon: STABLE_DEFAULT_ICON },
  legacy: { color: '#9c4221', icon: 'archive' },
};

export const TAG_ICON_MAP: Record<string, string> = {
  science: 'atom',
  research: 'flask-conical',
  history: 'landmark',
  law: 'gavel',
  finance: 'coins',
  design: 'palette',
  ai: 'circuit-board',
  security: 'shield',
};
