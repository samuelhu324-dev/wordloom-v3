export const supportedLanguages = ['zh-CN', 'en-US'] as const;

export type SupportedLanguage = (typeof supportedLanguages)[number];

export const defaultLanguage: SupportedLanguage = 'zh-CN';

export const STORAGE_KEY = 'wordloom.uiLanguage';

export function isSupportedLanguage(value: unknown): value is SupportedLanguage {
  return typeof value === 'string' && supportedLanguages.includes(value as SupportedLanguage);
}
