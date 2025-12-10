"use client";

import React from 'react';
import blockListStyles from '@/features/block/ui/BlockList.module.css';
import deletedPanelStyles from '@/features/block/ui/DeletedBlocksPanel.module.css';
import editorStyles from '@/modules/book-editor/ui/bookEditor.module.css';
import pageStyles from './spacingTest.module.css';

type BlockKind = 'paragraph' | 'heading' | 'quote' | 'bulleted_list' | 'numbered_list' | 'todo_list';

type BlockSample = {
  id: string;
  kind: BlockKind;
  text?: string;
  variant?: 'heading-1' | 'heading-2' | 'heading-3';
  listItems?: string[];
  todoItems?: Array<{ text: string; checked?: boolean; promoted?: boolean }>;
  quoteSource?: string;
};

type Scenario = {
  id: string;
  title: string;
  description: string;
  tokens: string[];
  hints: string[];
  blocks: BlockSample[];
};

type TokenScope = 'editor' | 'blocklist';

type TokenMetadata = {
  name: string;
  label: string;
  usage: string;
  scope?: TokenScope;
};

type BlockListScenario = {
  id: string;
  title: string;
  description: string;
  tokens: string[];
  hints: string[];
  attachProbe?: boolean;
  Preview: React.ForwardRefExoticComponent<React.RefAttributes<HTMLDivElement>>;
};

type ShellMatrixRow = {
  id: string;
  label: string;
  tokens: string[];
  hints: string[];
  blocks: BlockSample[];
};

const TOKEN_METADATA: TokenMetadata[] = [
  { name: '--wl-space-0', label: 'Space 0', usage: 'Primitive ladder start (0px)' },
  { name: '--wl-space-1', label: 'Space 1', usage: 'Primitive ladder 2px step' },
  { name: '--wl-space-2', label: 'Space 2', usage: 'Primitive ladder 4px step' },
  { name: '--wl-space-3', label: 'Space 3', usage: 'Primitive ladder 8px step' },
  { name: '--wl-space-4', label: 'Space 4', usage: 'Primitive ladder 12px step' },
  { name: '--wl-space-5', label: 'Space 5', usage: 'Primitive ladder 16px step' },
  { name: '--wl-space-6', label: 'Space 6', usage: 'Primitive ladder 20px step' },
  { name: '--wl-space-block-section', label: 'Block Section Gap', usage: 'Default .blockItem + .blockItem spacing' },
  { name: '--wl-space-block-tight', label: 'Block Tight Gap', usage: 'Paragraph/headings adjacency' },
  { name: '--wl-space-block-list-before', label: 'Canonical List Bridge (Before)', usage: 'Plan155A bridge token (no calc in components)' },
  { name: '--wl-space-block-list-before-safe-min', label: 'List Bridge Safe Min', usage: 'Row-gap lower bound (>= -tight)' },
  { name: '--wl-space-block-list-after', label: 'Canonical List Bridge (After)', usage: 'List exit cadence token' },
  { name: '--wl-space-list-before', label: 'List Bridge (Before)', usage: 'Text → list gap' },
  { name: '--wl-space-list-after', label: 'List Bridge (After)', usage: 'List → text gap' },
  { name: '--wl-space-todo-before', label: 'Todo Bridge (Before)', usage: 'Text → todo gap' },
  { name: '--wl-space-todo-after', label: 'Todo Bridge (After)', usage: 'Todo → text gap' },
  { name: '--wl-space-quote-before', label: 'Quote Bridge (Before)', usage: 'Heading/paragraph → quote gap' },
  { name: '--wl-space-quote-after', label: 'Quote Bridge (After)', usage: 'Quote → heading/paragraph gap' },
  { name: '--wl-space-inline', label: 'Inline Gap', usage: 'Inline rows, todo editors, list display rows' },
  { name: '--wl-block-shell-paragraph-padding-y', label: 'Paragraph Shell Padding', usage: 'Default block shell vertical padding (0px base)' },
  { name: '--wl-block-shell-heading-padding-top', label: 'Heading Shell Padding Top', usage: 'Additional breathing room before headings' },
  { name: '--wl-block-shell-heading-padding-bottom', label: 'Heading Shell Padding Bottom', usage: 'Additional breathing room after headings' },
  { name: '--wl-list-shell-padding-y', label: 'List Shell Padding Y', usage: 'Controls bulleted/numbered list vertical padding' },
  { name: '--wl-list-shell-padding-inline', label: 'List Shell Padding Inline', usage: 'List indent + marker gutter' },
  { name: '--wl-todo-shell-padding-y', label: 'Todo Shell Padding Y', usage: 'Vertical padding for todo shells' },
  { name: '--wl-quote-shell-padding-y', label: 'Quote Shell Padding Y', usage: 'Vertical padding for quote shells' },
  { name: '--wl-inline-insert-shell-padding-x', label: 'Inline Insert Padding X', usage: 'Horizontal padding for inline bars' },
  { name: '--wl-inline-insert-shell-padding-y', label: 'Inline Insert Padding Y', usage: 'Vertical padding for inline bars' },
  { name: '--wl-inline-list-shell-gap-y', label: 'Inline List Shell Gap', usage: 'Legacy row padding alias for inline rows' },
  { name: '--wl-inline-row-shell-padding-top', label: 'Inline Row Padding Top', usage: 'Top padding for inline list/todo rows' },
  { name: '--wl-inline-row-shell-padding-bottom', label: 'Inline Row Padding Bottom', usage: 'Bottom padding for inline list/todo rows' },
  { name: '--wl-editor-padding-y', label: 'Editor Shell Padding', usage: 'Outer breathing room for the document' },
  { name: '--wl-block-padding-left', label: 'Gutter Width', usage: 'Handle + marker gutter' },
  { name: '--wl-list-indent', label: 'List Indent', usage: 'Left padding for ul/ol containers' },
  { name: '--wl-list-item-gap', label: 'List Item Gap', usage: 'Spacing between li rows' },
  { name: '--wl-line-height-body', label: 'Line Height (Body)', usage: 'Paragraphs/headings baseline rhythm' },
  { name: '--wl-line-height-tight', label: 'Line Height (Tight)', usage: 'Todo/List/Quote internals' },
  { name: '--wl-line-height-list', label: 'Line Height (List/Todo)', usage: 'Shared display/edit token for Plan155A' },
  { name: '--wl-todo-checkbox-gap', label: 'Todo Checkbox Gap', usage: 'Space between checkbox and text' },
  { name: '--wl-todo-item-gap', label: 'Todo Item Gap (alias)', usage: 'Alias of --wl-list-item-gap; todo rows follow list rhythm' },
  { name: '--wl-quote-border-gap', label: 'Quote Border Gap', usage: 'Inset between border and quote text' },
  { name: '--wl-quote-padding-y', label: 'Quote Padding Y', usage: 'Vertical padding inside quote shell' },
  { name: '--wl-space-text-list', label: 'Legacy Text ↔ List', usage: 'Alias used during migration' },
  { name: '--wl-space-text-todo', label: 'Legacy Text ↔ Todo', usage: 'Alias used during migration' },
  { name: '--wl-blocklist-shell-gap', label: 'BlockList Shell Gap', usage: 'Gap between stacked cards', scope: 'blocklist' },
  { name: '--wl-blocklist-shell-padding-y', label: 'BlockList Padding Y', usage: 'Vertical breathing room inside the shell', scope: 'blocklist' },
  { name: '--wl-blocklist-shell-padding-x', label: 'BlockList Padding X', usage: 'Horizontal breathing room inside the shell', scope: 'blocklist' },
  { name: '--wl-blocklist-inline-offset', label: 'BlockList Inline Offset', usage: 'Handle + action gutter', scope: 'blocklist' },
  { name: '--wl-blocklist-card-gap', label: 'BlockList Card Gap', usage: 'Default .blockItem + .blockItem spacing', scope: 'blocklist' },
  { name: '--wl-blocklist-panel-padding', label: 'BlockList Panel Padding', usage: 'Inline insert + inspector padding', scope: 'blocklist' },
  { name: '--wl-blocklist-pill-padding-x', label: 'BlockList Pill Padding X', usage: 'Horizontal padding for chips/pills', scope: 'blocklist' },
  { name: '--wl-blocklist-pill-padding-y', label: 'BlockList Pill Padding Y', usage: 'Vertical padding for chips/pills', scope: 'blocklist' },
  { name: '--wl-space-2-5', label: 'Space 2.5', usage: 'Half-step (6px) bridging BlockList menus', scope: 'blocklist' },
  { name: '--wl-space-3-5', label: 'Space 3.5', usage: 'Half-step (10px) for inline popovers', scope: 'blocklist' },
  { name: '--wl-space-4-5', label: 'Space 4.5', usage: 'Half-step (14px) for cards/panels', scope: 'blocklist' },
];

const EDITOR_SCENARIOS: Scenario[] = [
  {
    id: 'section-tight-stack',
    title: 'Heading → Paragraph Flow',
      description: 'Adjacency margins on the editor shell own the tight rhythm while heading shells stay at zero padding.',
      tokens: ['--wl-space-block-tight', '--wl-block-shell-heading-padding-top', '--wl-block-shell-heading-padding-bottom'],
      hints: [
        'Margin overrides on .bookEditorShell collapse heading/paragraph stacks to --wl-space-block-tight (2px).',
        'Heading shells keep padding-y at 0px unless data attributes opt into section-scale spacing.',
        'Inspect the box model: the only contributor should be margin-top overrides, not residual <p>/<h2> UA margins.',
      ],
    blocks: [
      { id: 'heading-a', kind: 'heading', variant: 'heading-2', text: 'Quarterly Planning' },
      {
        id: 'paragraph-a',
        kind: 'paragraph',
        text: 'Establish one rhythm owner: .blockItem + .blockItem controls every inter-block distance.',
      },
      {
        id: 'paragraph-b',
        kind: 'paragraph',
        text: 'Paragraph stacks reuse the tight token so cursor jumps never change perceived spacing.',
      },
    ],
  },
  {
    id: 'list-sandwich',
    title: 'Paragraph → List → Paragraph',
      description: 'List shells take over internal padding while bridge tokens set asymmetric entry/exit gaps.',
      tokens: ['--wl-space-list-before', '--wl-space-list-after', '--wl-list-shell-padding-inline', '--wl-list-item-gap'],
      hints: [
        'Entry gaps equal --wl-space-list-before exactly, so computed margin-top should match the token value.',
        'List indent lives in --wl-list-shell-padding-inline so DevTools should only show padding-left, never margin.',
        'List rows reuse --wl-list-item-gap for li + li spacing inside the shell.',
        'Paragraph exiting the list reads --wl-space-list-after so lists stay tight above and roomy below.',
      ],
    blocks: [
      {
        id: 'paragraph-c',
        kind: 'paragraph',
        text: 'Use tight spacing before a bulleted list so it reads as the same narrative chunk.',
      },
      {
        id: 'list-bullets',
        kind: 'bulleted_list',
        listItems: ['Tokens live on the editor shell', 'Lists never ship browser default margins', 'li + li gap = 4px'],
      },
      {
        id: 'paragraph-d',
        kind: 'paragraph',
        text: 'When the list exits, spacing returns to tight mode before the next paragraph.',
      },
    ],
  },
  {
    id: 'quote-divider',
    title: 'Quote Cushion + Section Gap',
      description: 'Quotes mix before/after bridge tokens with shell padding for internal cushion.',
      tokens: ['--wl-space-quote-before', '--wl-space-quote-after', '--wl-quote-shell-padding-y', '--wl-quote-border-gap'],
      hints: [
        'Entry margin equals --wl-space-quote-before, so the computed gap should match the token value.',
        'Exiting the quote reuses --wl-space-quote-after; no generic section gap allowed.',
        'Inspect the quote body to confirm --wl-quote-shell-padding-y + --wl-quote-border-gap provide the vertical cushion.',
      ],
    blocks: [
      { id: 'heading-b', kind: 'heading', variant: 'heading-3', text: 'Research Signal' },
      {
        id: 'quote-a',
        kind: 'quote',
        text: 'Reset every browser margin before declaring the spacing system “fixed.”',
        quoteSource: 'Plan149A',
      },
      {
        id: 'paragraph-e',
        kind: 'paragraph',
        text: 'Quotes resume tight spacing when the following block is a paragraph.',
      },
    ],
  },
  {
    id: 'todo-stack',
    title: 'Todo Stack',
    description: 'Todo blocks combine a zero-width before bridge with their own row/checkbox tokens.',
    tokens: ['--wl-space-todo-before', '--wl-space-todo-after', '--wl-list-item-gap', '--wl-todo-checkbox-gap'],
    hints: [
      'Paragraph ↔ todo transitions stay micro-tight (0px) via --wl-space-todo-before.',
      'Todo rows reuse --wl-list-item-gap (via --wl-todo-item-gap alias) so Enter parity matches list blocks.',
      'Two todo blocks in a row now share --wl-space-todo-after instead of the generic inline gap.',
    ],
    blocks: [
      {
        id: 'paragraph-f',
        kind: 'paragraph',
        text: 'Todo lists inherit the tight bridge from paragraph blocks, just like lists.',
      },
      {
        id: 'todo-a',
        kind: 'todo_list',
        todoItems: [
          { text: 'Use --wl-todo-shell-padding-y for block padding.' },
          { text: 'Checkbox gap = --wl-todo-checkbox-gap.' },
        ],
      },
      {
        id: 'todo-b',
        kind: 'todo_list',
        todoItems: [
          { text: 'Document rules in VISUAL_RULES' },
          { text: 'Publish ADR-138 detailing Plan149 scope' },
        ],
      },
    ],
  },
];

const BlockListPreview = React.forwardRef<HTMLDivElement>((_, ref) => (
  <div
    ref={ref}
    className={blockListStyles.container}
    style={{ minHeight: 'auto', boxShadow: '0 18px 40px rgba(15, 23, 42, 0.12)' }}
  >
    <header className={pageStyles.blockListPreviewHeader}>
      <div>
        <p className={pageStyles.blockListPreviewLabel}>Block library</p>
        <p className={pageStyles.blockListPreviewSubhead}>Shell gap, inline gutter, and todo stack</p>
      </div>
      <span className={pageStyles.blockListPreviewBadge}>Plan152</span>
    </header>
    <div className={blockListStyles.list}>
      <div className={blockListStyles.blockItem} data-kind="heading">
        <div
          className={`${blockListStyles.textBlockShell} ${blockListStyles.textBlockShellHeading}`}
          data-heading-level="2"
        >
          <p className={`${blockListStyles.headingText} ${blockListStyles.headingLevel2}`}>Spacing Sweep</p>
        </div>
      </div>
      <div className={blockListStyles.blockItem} data-kind="paragraph">
        <div className={`${blockListStyles.textBlockShell} ${blockListStyles.textBlockShellParagraph}`}>
          <p className={blockListStyles.paragraphTextLine}>
            Block shell padding inherits --wl-blocklist-shell-padding-* for guaranteed breathing room.
          </p>
        </div>
      </div>
      <div className={blockListStyles.blockItem} data-kind="todo_list">
        <div className={blockListStyles.todoList}>
          <div className={blockListStyles.todoItem}>
            <span className={blockListStyles.todoText}>Todo rows reuse --block-gap-xs (2px) internally.</span>
          </div>
          <div className={blockListStyles.todoItem}>
            <span className={blockListStyles.todoText}>Inline gutter = --wl-blocklist-inline-offset.</span>
            <span className={blockListStyles.todoBadge}>CHECK</span>
          </div>
        </div>
      </div>
    </div>
  </div>
));

BlockListPreview.displayName = 'BlockListPreview';

const DeletedBlocksPreview = React.forwardRef<HTMLDivElement>((_, ref) => (
  <div ref={ref} className={deletedPanelStyles.panel} style={{ marginTop: 0 }}>
    <p className={deletedPanelStyles.title}>Deleted blocks</p>
    <ul className={deletedPanelStyles.list}>
      <li className={deletedPanelStyles.item}>
        <div className={deletedPanelStyles.row}>
          <span className={deletedPanelStyles.type}>QUOTE</span>
          <span className={deletedPanelStyles.preview}>“UA padding reset”</span>
          <button type="button" className={deletedPanelStyles.restoreBtn}>
            Restore
          </button>
        </div>
      </li>
      <li className={deletedPanelStyles.item}>
        <div className={deletedPanelStyles.row}>
          <span className={deletedPanelStyles.type}>TODO</span>
          <span className={deletedPanelStyles.preview}>Plan152 tokens audit</span>
          <button type="button" className={deletedPanelStyles.restoreBtn}>
            Restore
          </button>
        </div>
      </li>
    </ul>
  </div>
));

DeletedBlocksPreview.displayName = 'DeletedBlocksPreview';

const BLOCKLIST_SCENARIOS: BlockListScenario[] = [
  {
    id: 'blocklist-shell',
    title: 'BlockList Shell Rhythm',
    description: 'Mirrors the list container so QA can inspect shell padding, inline gutters, and todo stacks.',
    tokens: [
      '--wl-blocklist-shell-gap',
      '--wl-blocklist-shell-padding-y',
      '--wl-blocklist-shell-padding-x',
      '--wl-blocklist-inline-offset',
      '--wl-blocklist-card-gap',
    ],
    hints: [
      'Container gap equals shell padding; inspect the outer flex gap for 24px.',
      'Inline gutter removes mystery margins by padding .textBlockShell with --wl-blocklist-inline-offset.',
      'Todo rows collapse to --block-gap-xs (alias of --wl-space-1) for consistent micro stacks.',
    ],
    attachProbe: true,
    Preview: BlockListPreview,
  },
  {
    id: 'deleted-panel',
    title: 'Deleted Blocks Panel Density',
    description: 'Plan152 ladder also anchors the trash panel so restore buttons never drift.',
    tokens: [
      '--wl-blocklist-panel-padding',
      '--wl-blocklist-pill-padding-x',
      '--wl-blocklist-pill-padding-y',
      '--wl-space-3-5',
    ],
    hints: [
      'Panel padding now reads directly from --wl-blocklist-panel-padding so inline insert + trash share the same 20px cushion.',
      'Every chip/pill (tabs, badges, append buttons) inherits --wl-blocklist-pill-padding-x/y, so tweak once and re-run the sandbox.',
      'Row spacing still leans on --wl-space-3-5 for the readable stack; verify the computed margin stays 10px.',
    ],
    Preview: DeletedBlocksPreview,
  },
];

const SHELL_MATRIX_ROWS: ShellMatrixRow[] = [
  {
    id: 'matrix-list',
    label: 'Paragraph → List → Paragraph',
    tokens: ['--wl-space-block-tight', '--wl-space-list-before', '--wl-space-list-after', '--wl-list-shell-padding-y', '--wl-list-shell-padding-inline'],
    hints: [
      'Computed margin on the list block should equal --wl-space-list-before; no hidden calc().',
      'List shells pad themselves vertically via --wl-list-shell-padding-y so outer margins stay pure tokens.',
      'Paragraph exiting the list reads --wl-space-list-after to fan out the gap.',
    ],
    blocks: [
      {
        id: 'matrix-list-paragraph-a',
        kind: 'paragraph',
        text: 'Tight paragraph stack feeding into a bulleted list.',
      },
      {
        id: 'matrix-list-bullets',
        kind: 'bulleted_list',
        listItems: ['List shell padding via --wl-list-shell-padding-y', 'Bullets align through --wl-list-shell-padding-inline'],
      },
      {
        id: 'matrix-list-paragraph-b',
        kind: 'paragraph',
        text: 'Paragraph resumes the tight rhythm right after the list.',
      },
    ],
  },
  {
    id: 'matrix-todo',
    label: 'Paragraph → Todo → Paragraph',
    tokens: ['--wl-space-block-tight', '--wl-space-todo-before', '--wl-space-todo-after', '--wl-todo-shell-padding-y', '--wl-list-item-gap'],
    hints: [
      'Paragraph → todo gap equals --wl-space-todo-before (0px default) so the checklist hugs the copy.',
      'Todo shells own their inner padding with --wl-todo-shell-padding-y while adjacency margins stay outside.',
      'Two todos in a row reuse --wl-space-todo-after to keep the micro rhythm consistent.',
    ],
    blocks: [
      {
        id: 'matrix-todo-paragraph-a',
        kind: 'paragraph',
        text: 'Paragraph finishing a sentence before the checklist.',
      },
      {
        id: 'matrix-todo-block',
        kind: 'todo_list',
        todoItems: [
          { text: 'Shell padding stays inside the todo container.' },
          { text: 'Row gap = --wl-list-item-gap (alias --wl-todo-item-gap).' },
        ],
      },
      {
        id: 'matrix-todo-paragraph-b',
        kind: 'paragraph',
        text: 'Paragraph after the checklist should match the entry gap token.',
      },
    ],
  },
  {
    id: 'matrix-quote',
    label: 'Paragraph → Quote → Paragraph',
    tokens: ['--wl-space-block-tight', '--wl-space-quote-before', '--wl-space-quote-after', '--wl-quote-shell-padding-y'],
    hints: [
      'Quote entry gap equals --wl-space-quote-before directly on margin-top.',
      'Quote shells add their own padding via --wl-quote-shell-padding-y plus border gap.',
      'The exit paragraph mirrors --wl-space-quote-after so quotes read as single callouts.',
    ],
    blocks: [
      {
        id: 'matrix-quote-paragraph-a',
        kind: 'paragraph',
        text: 'Paragraph introducing the quote block.',
      },
      {
        id: 'matrix-quote-block',
        kind: 'quote',
        text: 'Shell tokens own the internal padding; bridges own the rhythm.',
        quoteSource: 'Plan153 Matrix',
      },
      {
        id: 'matrix-quote-paragraph-b',
        kind: 'paragraph',
        text: 'Paragraph exiting the quote returns to the tight rhythm using the after token.',
      },
    ],
  },
];

const SpacingTestPage: React.FC = () => {
  const editorProbeRef = React.useRef<HTMLElement>(null);
  const blockListProbeRef = React.useRef<HTMLDivElement>(null);

  const tokenValues = useTokenSnapshot(
    { editor: editorProbeRef, blocklist: blockListProbeRef },
    TOKEN_METADATA,
  );

  return (
    <main className={pageStyles.page} ref={editorProbeRef}>
      <section className={pageStyles.hero}>
        <h1 className={pageStyles.heroTitle}>Spacing System Testbed</h1>
        <p className={pageStyles.heroSubtitle}>
          Visual regression guard for the unified block spacing system. Every block here reuses the exact classes and
          tokens from <code>bookEditor.module.css</code> so designers, QA, and engineers can inspect real gutters instead of
          recreating them in Figma.
        </p>
        <div className={pageStyles.badgeRow}>
          <span className={pageStyles.badge}>VERTICAL-01 ~ 06</span>
          <span className={pageStyles.badge}>Plan152B rollout</span>
          <span className={pageStyles.badge}>CSS token probe</span>
        </div>
      </section>

      <section className={pageStyles.section}>
        <div>
          <h2 className={pageStyles.sectionTitle}>Token Snapshot</h2>
          <p className={pageStyles.sectionDescription}>
            Live values pulled from the actual components. Update a token once, refresh, and verify both the editor and
            BlockList ladders in one pass.
          </p>
        </div>
        <div className={pageStyles.tokenGrid}>
          {TOKEN_METADATA.map((token) => (
            <article key={token.name} className={pageStyles.tokenCard}>
              <span className={pageStyles.tokenName}>{token.name}</span>
              <span className={pageStyles.tokenValue}>{tokenValues[token.name] || '—'}</span>
              <span className={pageStyles.tokenUsage}>{token.usage}</span>
            </article>
          ))}
        </div>
      </section>

      <section className={pageStyles.section}>
        <div>
          <h2 className={pageStyles.sectionTitle}>Plan155A Guardrails</h2>
          <p className={pageStyles.sectionDescription}>
            Live checks for the no-jitter invariant (row-gap + before/after ≥ 0) and list typography parity between
            display and edit shells.
          </p>
        </div>
        <JitterGuardCard tokenValues={tokenValues} />
      </section>

      <section className={pageStyles.section}>
        <div>
          <h2 className={pageStyles.sectionTitle}>Editor Rhythm Scenarios</h2>
          <p className={pageStyles.sectionDescription}>
            Each card renders real blocks so you can diff tight vs section spacing, list bridges, quotes, and todos.
          </p>
        </div>
        <div className={pageStyles.scenarioGrid}>
          {EDITOR_SCENARIOS.map((scenario) => (
            <ScenarioCard key={scenario.id} scenario={scenario} />
          ))}
        </div>
      </section>

      <section className={pageStyles.section}>
        <div>
          <h2 className={pageStyles.sectionTitle}>Shell × Rhythm Matrix</h2>
          <p className={pageStyles.sectionDescription}>
            Screenshot Paragraph → List/Todo/Quote combos plus token readouts to prove shell padding and bridge tokens stay in
            sync between /dev/spacing-test and the real editor.
          </p>
        </div>
        <ShellMatrixCard />
      </section>

      <section className={pageStyles.section}>
        <div>
          <h2 className={pageStyles.sectionTitle}>BlockList + Trash Scenarios</h2>
          <p className={pageStyles.sectionDescription}>
            Mirrors the standalone BlockList shell and deleted-blocks panel so QA can probe the same Plan152 tokens
            outside the editor surface.
          </p>
        </div>
        <div className={pageStyles.scenarioGrid}>
          {BLOCKLIST_SCENARIOS.map((scenario) => (
            <BlockListScenarioCard
              key={scenario.id}
              scenario={scenario}
              probeRef={scenario.attachProbe ? blockListProbeRef : undefined}
            />
          ))}
        </div>
      </section>

      <section className={pageStyles.section}>
        <div className={pageStyles.noteCard}>
          <strong>Debug SOP:</strong> Select any suspicious gap, open DevTools → Computed → Box Model. If the highlighted
          margin/padding does not map back to one of the tokens listed above, file an issue before merging.
        </div>
      </section>
    </main>
  );
};

const ScenarioCard: React.FC<{ scenario: Scenario }> = ({ scenario }) => {
  return (
    <article className={pageStyles.scenarioCard}>
      <div className={pageStyles.scenarioHeader}>
        <h3 className={pageStyles.scenarioTitle}>{scenario.title}</h3>
        <p className={pageStyles.scenarioDescription}>{scenario.description}</p>
        <div className={pageStyles.tokenTagRow}>
          {scenario.tokens.map((token) => (
            <span key={token} className={pageStyles.tokenTag}>
              {token}
            </span>
          ))}
        </div>
      </div>
      <div className={pageStyles.blockDemoRoot}>
        <div className={pageStyles.blockDemoInner}>
          <div className={editorStyles.bookEditorShell}>
            {scenario.blocks.map((block) => (
              <BlockPreview key={block.id} block={block} />
            ))}
          </div>
        </div>
      </div>
      <ul className={pageStyles.hintList}>
        {scenario.hints.map((hint, index) => (
          <li key={`${scenario.id}-hint-${index}`}>{hint}</li>
        ))}
      </ul>
    </article>
  );
};

const JitterGuardCard: React.FC<{ tokenValues: Record<string, string> }> = ({ tokenValues }) => {
  const toNumber = (value?: string) => {
    if (!value) return Number.NaN;
    const parsed = parseFloat(value);
    return Number.isFinite(parsed) ? parsed : Number.NaN;
  };

  const formatPx = (value: number) => {
    if (!Number.isFinite(value)) return '—';
    const normalized = Math.abs(value) < 0.0001 ? 0 : value;
    const fixed = Number.isInteger(normalized) ? normalized.toString() : normalized.toFixed(2).replace(/\.00$/, '');
    return `${fixed}px`;
  };

  const tokenValue = (name: string) => tokenValues[name] || '—';

  const rowGap = toNumber(tokenValues['--wl-space-block-tight']);
  const listBefore = toNumber(tokenValues['--wl-space-block-list-before'] || tokenValues['--wl-space-list-before']);
  const listAfter = toNumber(tokenValues['--wl-space-block-list-after'] || tokenValues['--wl-space-list-after']);
  const beforeSum = rowGap + listBefore;
  const afterSum = rowGap + listAfter;

  const listLine = toNumber(tokenValues['--wl-line-height-list']);
  const tightLine = toNumber(tokenValues['--wl-line-height-tight']);
  const lineDiff = Math.abs(listLine - tightLine);

  const guards = [
    {
      id: 'list-entry',
      title: 'Paragraph → List (row-gap + before)',
      summary: formatPx(beforeSum),
      detail: `${tokenValue('--wl-space-block-tight')} + ${tokenValue('--wl-space-block-list-before')} = ${formatPx(beforeSum)} ≥ 0px`,
      safe: Number.isFinite(beforeSum) && beforeSum >= 0,
    },
    {
      id: 'list-exit',
      title: 'List → Paragraph (row-gap + after)',
      summary: formatPx(afterSum),
      detail: `${tokenValue('--wl-space-block-tight')} + ${tokenValue('--wl-space-block-list-after')} = ${formatPx(afterSum)} ≥ 0px`,
      safe: Number.isFinite(afterSum) && afterSum >= 0,
    },
    {
      id: 'line-height',
      title: 'List/Todo line-height parity',
      summary:
        Number.isFinite(listLine) && Number.isFinite(tightLine)
          ? `${tokenValue('--wl-line-height-list')} ≈ ${tokenValue('--wl-line-height-tight')}`
          : '—',
      detail: 'Display and edit states share --wl-line-height-list (target: --wl-line-height-tight).',
      safe: Number.isFinite(listLine) && Number.isFinite(tightLine) && lineDiff <= 0.01,
    },
  ];

  return (
    <article className={`${pageStyles.scenarioCard} ${pageStyles.guardCard}`}>
      <div className={pageStyles.guardMetrics}>
        {guards.map((guard) => (
          <div key={guard.id} className={pageStyles.guardMetric}>
            <div className={pageStyles.guardMetricTitle}>{guard.title}</div>
            <div className={pageStyles.guardMetricSummary}>{guard.summary}</div>
            <div className={pageStyles.guardMetricDetail}>{guard.detail}</div>
            <span className={pageStyles.guardStatus} data-state={guard.safe ? 'safe' : 'alert'}>
              {guard.safe ? 'Safe' : 'Needs attention'}
            </span>
          </div>
        ))}
      </div>
    </article>
  );
};

const ShellMatrixCard: React.FC = () => {
  return (
    <article className={pageStyles.scenarioCard}>
      <div className={pageStyles.scenarioHeader}>
        <h3 className={pageStyles.scenarioTitle}>Shell × Rhythm Matrix</h3>
        <p className={pageStyles.scenarioDescription}>
          Paragraph-anchored combos for screenshots. Capture Paragraph → List/Todo/Quote sequences with token readouts
          before merging spacing PRs.
        </p>
      </div>
      {SHELL_MATRIX_ROWS.map((row) => (
        <div key={row.id} className={pageStyles.matrixRow}>
          <div className={pageStyles.matrixRowHeader}>
            <p className={pageStyles.matrixRowLabel}>{row.label}</p>
            <div className={pageStyles.tokenTagRow}>
              {row.tokens.map((token) => (
                <span key={`${row.id}-${token}`} className={pageStyles.tokenTag}>
                  {token}
                </span>
              ))}
            </div>
          </div>
          <div className={pageStyles.blockDemoRoot}>
            <div className={pageStyles.blockDemoInner}>
              <div className={editorStyles.bookEditorShell}>
                {row.blocks.map((block) => (
                  <BlockPreview key={`${row.id}-${block.id}`} block={block} />
                ))}
              </div>
            </div>
          </div>
          <ul className={pageStyles.hintList}>
            {row.hints.map((hint, index) => (
              <li key={`${row.id}-hint-${index}`}>{hint}</li>
            ))}
          </ul>
        </div>
      ))}
    </article>
  );
};

const BlockListScenarioCard: React.FC<{
  scenario: BlockListScenario;
  probeRef?: React.RefObject<HTMLDivElement>;
}> = ({ scenario, probeRef }) => {
  const Preview = scenario.Preview;
  const previewRef: React.Ref<HTMLDivElement> | null = scenario.attachProbe ? probeRef ?? null : null;

  return (
    <article className={pageStyles.scenarioCard}>
      <div className={pageStyles.scenarioHeader}>
        <h3 className={pageStyles.scenarioTitle}>{scenario.title}</h3>
        <p className={pageStyles.scenarioDescription}>{scenario.description}</p>
        <div className={pageStyles.tokenTagRow}>
          {scenario.tokens.map((token) => (
            <span key={token} className={pageStyles.tokenTag}>
              {token}
            </span>
          ))}
        </div>
      </div>
      <div className={pageStyles.blockDemoRoot}>
        <div className={pageStyles.blockDemoInner}>
          <Preview ref={previewRef} />
        </div>
      </div>
      <ul className={pageStyles.hintList}>
        {scenario.hints.map((hint, index) => (
          <li key={`${scenario.id}-hint-${index}`}>{hint}</li>
        ))}
      </ul>
    </article>
  );
};

const BlockPreview: React.FC<{ block: BlockSample }> = ({ block }) => {
  return (
    <div className={editorStyles.blockItem} data-kind={block.kind}>
      <div className={editorStyles.blockItemMain}>{renderBlockBody(block)}</div>
    </div>
  );
};

const renderBlockBody = (block: BlockSample) => {
  if (block.kind === 'bulleted_list' || block.kind === 'numbered_list') {
    const ordered = block.kind === 'numbered_list';
    const markerClass = ordered ? editorStyles.inlineMarkerOrdered : editorStyles.inlineMarkerBullet;
    const items = block.listItems?.length ? block.listItems : ['List item'];
    return (
      <div className={editorStyles.todoList} role="list">
        {items.map((item, index) => (
          <div key={`${block.id}-${index}`} className={editorStyles.inlineRow}>
            <span className={`${editorStyles.inlineMarker} ${markerClass}`}>{ordered ? index + 1 : '•'}</span>
            <span className={editorStyles.todoText}>{item}</span>
          </div>
        ))}
      </div>
    );
  }

  if (block.kind === 'todo_list') {
    const rows = block.todoItems?.length ? block.todoItems : [{ text: 'Todo row' }];
    return (
      <div className={editorStyles.todoList} role="group">
        {rows.map((item, index) => (
          <div
            key={`${block.id}-todo-${index}`}
            className={`${editorStyles.inlineRow} ${editorStyles.todoRow} ${editorStyles.todoListItem}`}
          >
            <input type="checkbox" className={editorStyles.todoCheckbox} checked={Boolean(item.checked)} readOnly />
            <span
              className={`${editorStyles.todoText} ${item.checked ? editorStyles.todoTextChecked : ''}`.trim()}
            >
              {item.text}
            </span>
            {item.promoted && <span className={editorStyles.todoBadge}>PROMO</span>}
          </div>
        ))}
      </div>
    );
  }

  if (block.kind === 'quote') {
    return (
      <div className={editorStyles.quoteBlock}>
        <p>{block.text}</p>
        {block.quoteSource && <p style={{ fontSize: '13px', color: '#6b7280', margin: 0 }}>— {block.quoteSource}</p>}
      </div>
    );
  }

  const headingClass = block.variant ? editorStyles[block.variant] : '';

  return (
    <div className={editorStyles.textBlockShell}>
      <div className={`${editorStyles.textBlockContent} ${headingClass ?? ''}`.trim()}>{block.text}</div>
    </div>
  );
};

const useTokenSnapshot = (
  refs: Partial<Record<TokenScope, React.RefObject<HTMLElement>>>,
  metadata: TokenMetadata[],
) => {
  const [values, setValues] = React.useState<Record<string, string>>({});

  React.useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const snapshot: Record<string, string> = {};
    metadata.forEach((token) => {
      const scope = token.scope ?? 'editor';
      const node = refs[scope]?.current;
      if (!node) {
        snapshot[token.name] = '';
        return;
      }
      snapshot[token.name] = window.getComputedStyle(node).getPropertyValue(token.name).trim();
    });
    setValues(snapshot);
  }, [refs.editor?.current, refs.blocklist?.current, metadata]);

  return values;
};

export default SpacingTestPage;
