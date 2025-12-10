const path = require('path');

const ALLOWED_FILES = [
  /book-editor[\\/]+model[\\/]+caretDomUtils\.ts$/,
  /book-editor[\\/]+model[\\/]+caretDomUtils\.tsx$/,
  /book-editor[\\/]+model[\\/]+__tests__[\\/]+caretDomUtils\.test\.tsx?$/,
  /book-editor[\\/]+model[\\/]+__tests__[\\/]+caretDomUtils\.spec\.tsx?$/,
];

const normalize = (filename) => filename.split(path.sep).join('/');

const isAllowedFile = (filename) => ALLOWED_FILES.some((regex) => regex.test(filename));

const isGetSelectionCall = (node) => {
  if (node.callee.type === 'Identifier') {
    return node.callee.name === 'getSelection';
  }
  if (node.callee.type === 'MemberExpression' && !node.callee.computed) {
    const property = node.callee.property;
    return property.type === 'Identifier' && property.name === 'getSelection';
  }
  return false;
};

module.exports = {
  rules: {
    'caret-selection-owner': {
      meta: {
        type: 'problem',
        docs: {
          description: 'Restrict direct window/document.getSelection() usage to caretDomUtils',
          recommended: false,
        },
        messages: {
          restricted: 'window/document.getSelection() is reserved for caretDomUtils per Plan164. Use caretDomUtils helpers instead.',
        },
        schema: [],
      },
      create(context) {
        const filename = normalize(context.getFilename());
        if (isAllowedFile(filename)) {
          return {};
        }

        return {
          CallExpression(node) {
            if (isGetSelectionCall(node)) {
              context.report({ node, messageId: 'restricted' });
            }
          },
        };
      },
    },
  },
};
