import React, { useState } from 'react'
import { BlockDto } from '@/entities/block'
import { BlockList, BlockEditor } from '@/features/block'
import { Button } from '@/shared/ui'
import styles from './BlockMainWidget.module.css'

interface BlockMainWidgetProps {
  blocks: BlockDto[]
  isLoading?: boolean
  onSelectBlock?: (id: string) => void
  onBlockUpdate?: (blockId: string, content: string) => Promise<void>
}

export const BlockMainWidget = React.forwardRef<HTMLDivElement, BlockMainWidgetProps>(
  ({ blocks, isLoading, onSelectBlock, onBlockUpdate }, ref) => {
    const [editingBlockId, setEditingBlockId] = useState<string | null>(null)

    const handleBlockSelect = (blockId: string) => {
      setEditingBlockId(blockId)
      onSelectBlock?.(blockId)
    }

    const handleBlockSave = async (content: string) => {
      if (editingBlockId && onBlockUpdate) {
        await onBlockUpdate(editingBlockId, content)
        setEditingBlockId(null)
      }
    }

    const handleCancel = () => {
      setEditingBlockId(null)
    }

    const editingBlock = editingBlockId ? blocks.find((b) => b.id === editingBlockId) : null

    return (
      <div ref={ref} className={styles.widget}>
        {editingBlock ? (
          // Editor Mode
          <div className={styles.editorContainer}>
            <BlockEditor
              block={editingBlock}
              onSave={handleBlockSave}
              isLoading={isLoading}
              onCancel={handleCancel}
            />
          </div>
        ) : (
          // List Mode
          <>
            <div className={styles.header}>
              <h2>Blocks</h2>
              <Button variant="primary">+ New</Button>
            </div>
            <BlockList
              blocks={blocks}
              isLoading={isLoading}
              onSelectBlock={handleBlockSelect}
            />
          </>
        )}
      </div>
    )
  }
)

BlockMainWidget.displayName = 'BlockMainWidget'

