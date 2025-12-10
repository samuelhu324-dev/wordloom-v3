/**
 * Custom ESLint Rule: no-raw-fetch-host
 *
 * Disallows calling fetch() with absolute backend URLs or prefixed API paths.
 * Enforces usage of relative resource paths (e.g. '/books') via shared axios client (api.*)
 * or a thin wrapper instead of raw fetch with hardcoded host/port.
 *
 * Blocked patterns:
 *   fetch('http://localhost:30001/api/v1/books')
 *   fetch('https://172.31.')
 *   fetch('http://172.31.150.143:30001/...')
 *   fetch('/api/v1/books/deleted')  (duplicate prefix; client already adds it)
 *
 * Allowed:
 *   fetch('/health')              // If explicitly whitelisted (internal only)
 *   api.get('/books')             // Preferred
 *
 * Configuration: enabled as 'error' in .eslintrc.json
 */

module.exports = {
  rules: {
    'no-raw-fetch-host': {
      meta: {
        type: 'problem',
        docs: {
          description: 'Disallow raw fetch with absolute backend host or duplicate /api/v1 prefix',
          recommended: false,
        },
        messages: {
          absolute: 'Do not use raw fetch with absolute backend URL: {{url}}. Use api.get/post with relative path.',
          duplicatePrefix: 'Path {{url}} contains /api/v1 prefix; base client already includes it. Remove the prefix.',
        },
        schema: [],
      },
      create(context) {
        return {
          CallExpression(node) {
            if (node.callee.type !== 'Identifier' || node.callee.name !== 'fetch') return;
            if (!node.arguments.length) return;
            const arg = node.arguments[0];
            if (arg.type !== 'Literal' || typeof arg.value !== 'string') return;
            const url = arg.value;
            // Absolute host detection
            if (/^https?:\/\//i.test(url) && /(localhost|\d+\.\d+\.\d+\.\d+)(:30001)?/.test(url)) {
              context.report({ node: arg, messageId: 'absolute', data: { url } });
              return;
            }
            // Duplicate prefix detection
            if (url.startsWith('/api/v1/')) {
              context.report({ node: arg, messageId: 'duplicatePrefix', data: { url } });
            }
          },
        };
      },
    },
  },
};
