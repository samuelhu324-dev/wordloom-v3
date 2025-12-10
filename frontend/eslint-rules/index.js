// ESLint Plugin entry: wordloom-custom
// Aggregates all custom rules for Wordloom frontend.
const fetchRules = require('./no-raw-fetch-host');
const selectionRules = require('./selection-command-scope');
const caretRules = require('./caret-selection-owner');

module.exports = {
	rules: {
		...fetchRules.rules,
		...selectionRules.rules,
		...caretRules.rules,
	},
};
