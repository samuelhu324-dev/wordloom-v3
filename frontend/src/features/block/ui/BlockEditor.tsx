'use client'

import React, { useCallback, useState, useMemo } from 'react'
import { createEditor, Descendant, Editor } from 'slate'
import { Slate, Editable, withReact } from 'slate-react'
import { withHistory } from 'slate-history'
import { BlockDto } from '@/entities/block'
import styles from './BlockEditor.module.css'

interface BlockEditorProps {
  block: BlockDto
  onSave?: (content: string) => Promise<void>
  isLoading?: boolean
  onCancel?: () => void
}

/**
 * BlockEditor Component - Slate.js Integration
 *
 * Rich text editor for Wordloom blocks using Slate.js
 * Supports:
 * - Text formatting: Bold, Italic, Underline
 * - Keyboard shortcuts: Ctrl+B, Ctrl+I, Ctrl+U
 * - Toolbar with formatting buttons
 * - Save/Cancel operations with loading states
 * - Character count and block metadata display
 *
 * Architecture:
 * - Slate.js as core editor engine
 * - Slate-react for React integration
 * - Slate-history for undo/redo
 *
 * Future enhancements (Phase 6+):
 * - Block type switching (Heading, Code, etc)
 * - List handling (ordered/unordered)
 * - Media insertion (images, videos)
 * - Link support
 * - Collaborative editing (via Yjs)
 */

const DEFAULT_INITIAL_VALUE: Descendant[] = [
  {
    type: 'paragraph',
    children: [{ text: '' }],
  } as any,
]

export const BlockEditor = React.forwardRef<HTMLDivElement, BlockEditorProps>(
  ({ block, onSave, isLoading = false, onCancel }, ref) => {
    // Initialize editor with history support (undo/redo)
    const editor = useMemo(() => withHistory(withReact(createEditor())), [])
    const [value, setValue] = useState<Descendant[]>(DEFAULT_INITIAL_VALUE)
    const [isSaving, setIsSaving] = useState(false)
    const [charCount, setCharCount] = useState(0)

    // Update character count when value changes
    React.useEffect(() => {
      const text = value
        .map((node) => extractText(node))
        .join('')
      setCharCount(text.length)
    }, [value])

    // Toggle mark formatting (bold, italic, underline)
    const handleToggleMark = useCallback(
      (mark: 'bold' | 'italic' | 'underline') => {
        const isActive = isMarkActive(editor, mark)

        if (isActive) {
          Editor.removeMark(editor, mark)
        } else {
          Editor.addMark(editor, mark, true)
        }
      },
      [editor]
    )

    // Save content to backend
    const handleSave = useCallback(async () => {
      if (!onSave) return

      setIsSaving(true)
      try {
        const content = value
          .map((node) => extractText(node))
          .join('\n')
        await onSave(content)
      } catch (error) {
        console.error('Failed to save block:', error)
      } finally {
        setIsSaving(false)
      }
    }, [value, onSave])

    return (
      <div ref={ref} className={styles.editor}>
        {/* Toolbar */}
        <div className={styles.toolbar}>
          <div className={styles.toolbarInfo}>
            <span className={styles.blockType}>{block.type?.toUpperCase() || 'TEXT'}</span>
          </div>
          <div className={styles.toolbarActions}>
            <button
              className={styles.formatBtn}
              onMouseDown={(e) => {
                e.preventDefault()
                handleToggleMark('bold')
              }}
              title="Bold (Ctrl+B)"
              disabled={isLoading || isSaving}
            >
              <strong>B</strong>
            </button>

            <button
              className={styles.formatBtn}
              onMouseDown={(e) => {
                e.preventDefault()
                handleToggleMark('italic')
              }}
              title="Italic (Ctrl+I)"
              disabled={isLoading || isSaving}
            >
              <em>I</em>
            </button>

            <button
              className={styles.formatBtn}
              onMouseDown={(e) => {
                e.preventDefault()
                handleToggleMark('underline')
              }}
              title="Underline (Ctrl+U)"
              disabled={isLoading || isSaving}
            >
              <u>U</u>
            </button>

            <div style={{ width: '1px', background: 'var(--color-border)', margin: '0 0.5rem' }} />

            {onSave && (
              <button
                className={styles.button}
                onClick={handleSave}
                disabled={isLoading || isSaving}
              >
                {isSaving ? '保存中...' : '保存'}
              </button>
            )}

            {onCancel && (
              <button
                className={`${styles.button} ${styles.secondary}`}
                onClick={onCancel}
                disabled={isLoading || isSaving}
              >
                取消
              </button>
            )}
          </div>
        </div>

        {/* Editor Content */}
        <div className={styles.editorContent}>
          <Slate
            editor={editor}
            initialValue={value}
            onChange={(newValue) => setValue(newValue)}
          >
            <Editable
              className={styles.editableArea}
              placeholder="开始输入..."
              onKeyDown={(event) => handleKeyDown(event, editor)}
              disabled={isLoading || isSaving}
              renderLeaf={renderLeaf}
            />
          </Slate>
        </div>

        {/* Status Bar */}
        <div className={styles.statusBar}>
          <span className={styles.charCount}>
            字符数: {charCount}
          </span>
          <span className={styles.blockId}>
            Block ID: {block.id?.substring(0, 8)}...
          </span>
        </div>
      </div>
    )
  }
)

BlockEditor.displayName = 'BlockEditor'

// ============================================
// Helpers
// ============================================

/**
 * Check if a mark is active in the current selection
 */
function isMarkActive(editor: Editor, format: string): boolean {
  const marks = Editor.marks(editor)
  return marks ? marks[format as keyof typeof marks] === true : false
}

/**
 * Extract all text from a node recursively
 */
function extractText(node: any): string {
  if (typeof node === 'string') {
    return node
  }
  if (node.text) {
    return node.text
  }
  if (node.children && Array.isArray(node.children)) {
    return node.children.map((child: any) => extractText(child)).join('')
  }
  return ''
}

/**
 * Handle keyboard shortcuts for formatting
 */
function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>, editor: Editor) {
  if (!event.ctrlKey && !event.metaKey) {
    return
  }

  switch (event.key) {
    case 'b':
      event.preventDefault()
      Editor.addMark(editor, 'bold', true)
      break
    case 'i':
      event.preventDefault()
      Editor.addMark(editor, 'italic', true)
      break
    case 'u':
      event.preventDefault()
      Editor.addMark(editor, 'underline', true)
      break
  }
}

/**
 * Render leaf nodes with formatting marks
 */
function renderLeaf(props: any) {
  const { attributes, children, leaf } = props

  let el = children

  if (leaf.bold) {
    el = <strong>{el}</strong>
  }

  if (leaf.italic) {
    el = <em>{el}</em>
  }

  if (leaf.underline) {
    el = <u>{el}</u>
  }

  return <span {...attributes}>{el}</span>
}
