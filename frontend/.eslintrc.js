module.exports = {
  extends: ['next/core-web-vitals'],
  plugins: ['wordloom-custom'],
  rules: {
    'wordloom-custom/no-raw-fetch-host': 'error',
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: ['@/features/block/legacy/*'],
            message: 'Legacy block editor modules are read-only; use modules/book-editor entry points instead.',
          },
        ],
      },
    ],
  },
};
