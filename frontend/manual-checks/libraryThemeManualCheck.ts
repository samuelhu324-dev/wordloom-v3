import { getBookTheme } from '@/shared/theme/theme-pure';

const samples = [
  {
    name: 'withExplicitThemeColor',
    input: {
      id: 'book-001',
      title: 'Manual Theme Check',
      stage: 'seed' as const,
      legacyFlag: false,
      coverColor: '#3B82F6',
      libraryColorSeed: 'library-abc',
    },
  },
  {
    name: 'fallbackToSeed',
    input: {
      id: 'book-002',
      title: 'Fallback Check',
      stage: 'seed' as const,
      legacyFlag: false,
      libraryColorSeed: 'library-abc',
    },
  },
];

for (const sample of samples) {
  const theme = getBookTheme(sample.input);
  console.log(sample.name, theme.accentColor, theme.glyph);
}
