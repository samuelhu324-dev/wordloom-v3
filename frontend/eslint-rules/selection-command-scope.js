/**
 * Custom ESLint Rule: selection-command-scope
 *
 * Guards autosave/selection separation by preventing components/hooks from importing
 * low-level selection intents (requestSelectionEdge/requestSelectionOffset/selectionStore)
 * outside of the structural command layer. Only BlockEditor command modules may
 * manipulate caret intents directly; everyone else must go through blockCommands APIs.
 */

const path = require('path');

const BANNED_SPECIFIERS = new Set(['requestSelectionEdge', 'requestSelectionOffset', 'selectionStore']);
const ALLOWED_FILES = [
  /book-editor[\\/]+model[\\/]+blockCommands\.tsx?$/,
  /book-editor[\\/]+model[\\/]+selectionStore\.tsx?$/,
  /book-editor[\\/]+ui[\\/]+BlockEditorCore\.tsx?$/,
];

const normalize = (filename) => filename.split(path.sep).join('/');

const matchesAllowedFile = (filename) => ALLOWED_FILES.some((regex) => regex.test(filename));

module.exports = {
  rules: {
    'selection-command-scope': {
      meta: {
        type: 'problem',
        docs: {
          description:
            'Disallow importing selectionStore command helpers outside structural block commands',
          recommended: false,
        },
        messages: {
          restricted:
            'Selection intents ({{name}}) must be requested via blockCommands. Importing from selectionStore outside command modules breaks caret stability.',
        },
        schema: [],
      },
      create(context) {
        const filename = normalize(context.getFilename());
        if (matchesAllowedFile(filename)) {
          return {};
        }

        const reportInvalidSpecifier = (specifier, name) => {
          context.report({ node: specifier, messageId: 'restricted', data: { name } });
        };

        const inspectSpecifiers = (specifiers) => {
          specifiers.forEach((spec) => {
            if (spec.type === 'ImportSpecifier') {
              const importedName = spec.imported.name;
              if (BANNED_SPECIFIERS.has(importedName)) {
                reportInvalidSpecifier(spec, importedName);
              }
            } else if (spec.type === 'ImportNamespaceSpecifier' || spec.type === 'ImportDefaultSpecifier') {
              // Block namespace/default imports that could expose restricted members
              reportInvalidSpecifier(spec, 'selectionStore');
            }
          });
        };

        const isSelectionStoreModule = (sourceValue) => {
          if (typeof sourceValue !== 'string') {
            return false;
          }
          return /selectionStore$/.test(sourceValue);
        };

        return {
          ImportDeclaration(node) {
            if (!isSelectionStoreModule(node.source.value)) {
              return;
            }
            inspectSpecifiers(node.specifiers);
          },
          CallExpression(node) {
            if (
              node.callee.type === 'Identifier' &&
              node.callee.name === 'require' &&
              node.arguments.length === 1
            ) {
              const arg = node.arguments[0];
              if (arg.type === 'Literal' && isSelectionStoreModule(arg.value)) {
                // require('.../selectionStore') is entirely disallowed outside allowed files
                context.report({ node: arg, messageId: 'restricted', data: { name: 'selectionStore' } });
              }
            }
          },
        };
      },
    },
  },
};
