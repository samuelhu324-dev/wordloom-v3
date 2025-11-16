/**
 * Theme System: 3 themes × 2 modes
 * - Light (light mode + dark mode)
 * - Dark (light mode + dark mode)
 * - Loom (灰蓝, light mode + dark mode)
 *
 * Generates CSS Variables for dynamic theme switching
 */

export type ThemeName = 'Light' | 'Dark' | 'Loom';
export type ThemeMode = 'light' | 'dark';

export interface ThemeColors {
  primary: string;
  primaryLight: string;
  secondary: string;
  tertiary?: string;
  surface: string;
  surfaceAlt: string;
  muted: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  text: string;
  textSecondary: string;
  textMuted: string;
}

export const themes: Record<ThemeName, Record<ThemeMode, ThemeColors>> = {
  Light: {
    light: {
      primary: '#1F2937',
      primaryLight: '#374151',
      secondary: '#6366F1',
      surface: '#FFFFFF',
      surfaceAlt: '#F9FAFB',
      muted: '#9CA3AF',
      border: '#E5E7EB',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
      text: '#111827',
      textSecondary: '#6B7280',
      textMuted: '#9CA3AF',
    },
    dark: {
      primary: '#F3F4F6',
      primaryLight: '#E5E7EB',
      secondary: '#A5B4FC',
      surface: '#1F2937',
      surfaceAlt: '#111827',
      muted: '#6B7280',
      border: '#374151',
      success: '#34D399',
      warning: '#FBBF24',
      error: '#F87171',
      info: '#60A5FA',
      text: '#F9FAFB',
      textSecondary: '#D1D5DB',
      textMuted: '#9CA3AF',
    },
  },
  Dark: {
    light: {
      primary: '#F3F4F6',
      primaryLight: '#E5E7EB',
      secondary: '#A5B4FC',
      surface: '#111827',
      surfaceAlt: '#1F2937',
      muted: '#6B7280',
      border: '#374151',
      success: '#34D399',
      warning: '#FBBF24',
      error: '#F87171',
      info: '#60A5FA',
      text: '#F9FAFB',
      textSecondary: '#D1D5DB',
      textMuted: '#9CA3AF',
    },
    dark: {
      primary: '#F3F4F6',
      primaryLight: '#E5E7EB',
      secondary: '#A5B4FC',
      surface: '#0F172A',
      surfaceAlt: '#111827',
      muted: '#475569',
      border: '#334155',
      success: '#22C55E',
      warning: '#FBBF24',
      error: '#EF4444',
      info: '#3B82F6',
      text: '#F1F5F9',
      textSecondary: '#CBD5E1',
      textMuted: '#94A3B8',
    },
  },
  Loom: {
    light: {
      primary: '#2C3E50',
      primaryLight: '#34495E',
      secondary: '#3498DB',
      tertiary: '#16A085',
      surface: '#ECF0F1',
      surfaceAlt: '#F8F9FA',
      muted: '#7F8C8D',
      border: '#BDC3C7',
      success: '#27AE60',
      warning: '#F39C12',
      error: '#E74C3C',
      info: '#3498DB',
      text: '#2C3E50',
      textSecondary: '#7F8C8D',
      textMuted: '#95A5A6',
    },
    dark: {
      primary: '#ECF0F1',
      primaryLight: '#BDC3C7',
      secondary: '#3498DB',
      tertiary: '#1ABC9C',
      surface: '#1A252F',
      surfaceAlt: '#0F1419',
      muted: '#34495E',
      border: '#2C3E50',
      success: '#2ECC71',
      warning: '#E67E22',
      error: '#E74C3C',
      info: '#3498DB',
      text: '#ECF0F1',
      textSecondary: '#BDC3C7',
      textMuted: '#7F8C8D',
    },
  },
};

/**
 * Generate CSS Variables from theme colors
 * Output: --color-primary, --color-secondary, etc.
 */
export function generateCSSVariables(colors: ThemeColors): string {
  const variables = Object.entries(colors)
    .map(([key, value]) => `--color-${key}: ${value}`)
    .join(';\n  ');
  return variables + ';';
}

/**
 * Get all available themes
 */
export function getAvailableThemes(): ThemeName[] {
  return Object.keys(themes) as ThemeName[];
}

/**
 * THEMES constant for easier access
 */
export const THEMES = getAvailableThemes();
