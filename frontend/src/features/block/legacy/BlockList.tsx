'use client';

// LEGACY: Retained only for historical context. Prefer modules/book-editor entry points.
import React, { useImperativeHandle, useRef, useState } from 'react';
import { PlusCircle, Plus } from 'lucide-react';
import { useUpdateBlock } from '@/features/block/model/hooks';
import { BlockDto, BlockKind, BlockContent, serializeBlockContent } from '@/entities/block';
import { BlockRenderer } from './BlockRenderer';
import { COMMON_INSERT_ITEMS, EXTRA_INSERT_GROUPS, InsertMenuItemConfig } from './insertMenuConfig';
import { BlockInsertOptions, BlockInsertPosition, BlockInsertSource } from './insertTypes';
import styles from '../ui/BlockList.module.css';

const cloneBlockContent = (content: BlockContent): BlockContent => {
  if (content == null) {
    return content;
  }
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(content);
    } catch (error) {
      // ignore and fallback
    }
  }
  if (typeof content === 'object') {
    try {
      return JSON.parse(JSON.stringify(content)) as BlockContent;
    } catch (error) {
      return content;
    }
  }
  return content;
};


export interface BlockListHandle {
  saveAll: () => Promise<void>;
}

interface BlockListProps {
  blocks: BlockDto[];
  isLoading?: boolean;
  onBlockClick?: (blockId: string) => void;
  onBlockDelete?: (blockId: string) => void;
  onAddBlock?: (kind: BlockKind, options?: BlockInsertOptions) => void;
}

/**
 * BlockList
 * 用于 Book 详情页显示块列表
 * 特点：
 * - 垂直列表布局
 * - 每个块可编辑/删除
 * - 支持添加新块
 */
// 子组件：单个块（避免在 map 中直接使用 hooks 导致删除时 hook 数变化）
interface BlockItemProps {
  block: BlockDto;
  onDelete?: (id: string) => void;
  onClick?: (id: string) => void;
  onRegisterSave: (blockId: string, handler: () => Promise<void>) => void;
  onUnregisterSave: (blockId: string) => void;
  isEditing: boolean;
  onStartEdit: (id: string) => void;
  onExitEdit: (id: string) => void;
  onRequestInsert?: (payload: {
    blockId: string;
    kind: BlockKind;
    position: BlockInsertPosition;
    source: BlockInsertSource;
    headingLevel?: 1 | 2 | 3;
  }) => void;
  inlineMenuActive: boolean;
  inlineMenuPosition: BlockInsertPosition;
  onInlineMenuPositionChange: (position: BlockInsertPosition) => void;
  onToggleInlineMenu: (blockId: string) => void;
  inlineMenuMoreOpen: boolean;
  onToggleInlineMenuMore: () => void;
  inlineMenuRef: React.RefObject<HTMLDivElement>;
  onInlineMenuSelect: (item: InsertMenuItemConfig, position: BlockInsertPosition) => void;
  canInsert: boolean;
  previousBlockId?: string;
}

const useHoverIntent = (delay = 180) => {
  const [visible, setVisible] = React.useState(false);
  const timerRef = React.useRef<number | null>(null);

  const clearTimer = React.useCallback(() => {
    if (timerRef.current != null && typeof window !== 'undefined') {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const handleMouseEnter = React.useCallback(() => {
    if (typeof window === 'undefined') {
      setVisible(true);
      return;
    }
    clearTimer();
    timerRef.current = window.setTimeout(() => {
      setVisible(true);
      timerRef.current = null;
    }, delay);
  }, [clearTimer, delay]);

  const handleMouseLeave = React.useCallback(() => {
    clearTimer();
    setVisible(false);
  }, [clearTimer]);

  React.useEffect(() => () => clearTimer(), [clearTimer]);

  return {
    visible,
    bind: {
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave,
    } as React.HTMLAttributes<HTMLDivElement>,
  };
};

const BlockItem: React.FC<BlockItemProps> = ({
  block,
  onDelete,
  onClick,
  onRegisterSave,
  onUnregisterSave,
  isEditing,
  onStartEdit,
  onExitEdit,
  onRequestInsert,
  inlineMenuActive,
  inlineMenuPosition,
  onInlineMenuPositionChange,
  onToggleInlineMenu,
  inlineMenuMoreOpen,
  onToggleInlineMenuMore,
  inlineMenuRef,
  onInlineMenuSelect,
  canInsert,
  previousBlockId,
}) => {
  const [content, setContent] = useState<BlockContent>(() => cloneBlockContent(block.content));
  const [localKind, setLocalKind] = useState<BlockKind>(block.kind);
  const updateMutation = useUpdateBlock(block.id);
  const contentRef = useRef<BlockContent>(cloneBlockContent(block.content));
  const lastSavedContentRef = useRef<BlockContent>(cloneBlockContent(block.content));
  const lastSerializedRef = useRef<string>(serializeBlockContent(block.kind, block.content));
  const lastSavedKindRef = useRef<BlockKind>(block.kind);
  const editorRef = useRef<HTMLElement | null>(null);
  const hoverIntent = useHoverIntent(180);
  const isActive = isEditing;
  const showActions = canInsert && (isActive || hoverIntent.visible);

  const handleDeleteViaShortcut = React.useCallback(() => {
    if (!onDelete) return;
    onDelete(block.id);
    if (previousBlockId) {
      onStartEdit(previousBlockId);
    } else {
      onExitEdit(block.id);
    }
  }, [block.id, onDelete, onStartEdit, onExitEdit, previousBlockId]);

  React.useEffect(() => {
    contentRef.current = content;
  }, [content]);

  React.useEffect(() => {
    const nextContent = cloneBlockContent(block.content);
    const clonedForRefs = cloneBlockContent(block.content);
    lastSavedContentRef.current = clonedForRefs;
    lastSerializedRef.current = serializeBlockContent(block.kind, block.content);
    lastSavedKindRef.current = block.kind;

    if (isEditing) {
      return;
    }

    setContent(nextContent);
    contentRef.current = clonedForRefs;
    setLocalKind(block.kind);
  }, [block.content, block.kind, isEditing]);


  React.useEffect(() => {
    if (isEditing) {
      requestAnimationFrame(() => editorRef.current?.focus());
    }
  }, [isEditing]);

  const save = React.useCallback(async () => {
    const serialized = serializeBlockContent(localKind, contentRef.current);
    const kindChanged = localKind !== lastSavedKindRef.current;
    if (!kindChanged && serialized === lastSerializedRef.current) return;
    try {
      await updateMutation.mutateAsync({
        content: serialized,
        ...(kindChanged ? { kind: localKind } : {}),
      });
      lastSerializedRef.current = serialized;
      lastSavedContentRef.current = cloneBlockContent(contentRef.current);
      lastSavedKindRef.current = localKind;
    } catch (e) {
      console.error('保存失败', e);
    }
  }, [localKind, updateMutation]);

  React.useEffect(() => {
    onRegisterSave(block.id, save);
    return () => onUnregisterSave(block.id);
  }, [block.id, onRegisterSave, onUnregisterSave, save]);

  const handleChange = (nextContent: BlockContent) => {
    setContent(nextContent);
    contentRef.current = nextContent;
  };

  const handleCancelEdit = () => {
    const rollback = cloneBlockContent(lastSavedContentRef.current);
    setContent(rollback);
    contentRef.current = rollback;
    setLocalKind(lastSavedKindRef.current);
    onExitEdit(block.id);
  };

  const applyKindLocally = React.useCallback((nextKind: BlockKind, nextContent: BlockContent) => {
    setLocalKind(nextKind);
    const cloned = cloneBlockContent(nextContent);
    setContent(cloned);
    contentRef.current = cloned;
  }, []);

  const handleTransformKind = React.useCallback(async (nextKind: BlockKind, nextContent: BlockContent) => {
    applyKindLocally(nextKind, nextContent);
    try {
      const serialized = serializeBlockContent(nextKind, nextContent);
      await updateMutation.mutateAsync({ kind: nextKind, content: serialized });
      lastSerializedRef.current = serialized;
      lastSavedContentRef.current = cloneBlockContent(nextContent);
      lastSavedKindRef.current = nextKind;
    } catch (error) {
      console.error('切换块类型失败', error);
    }
  }, [applyKindLocally, updateMutation]);

  return (
    <div
      className={`${styles.blockItem} ${isEditing ? styles.blockItemEditing : ''}`}
      data-kind={localKind}
      tabIndex={0}
      onClick={() => onClick?.(block.id)}
      {...hoverIntent.bind}
    >
      <BlockRenderer
        block={{ ...block, kind: localKind }}
        content={content}
        isEditing={isEditing}
        editorRef={editorRef}
        onStartEdit={() => onStartEdit(block.id)}
        onChange={handleChange}
        onSave={save}
        onQuickSave={save}
        onExitEdit={() => onExitEdit(block.id)}
        onCancelEdit={handleCancelEdit}
        onDeleteBlock={handleDeleteViaShortcut}
        onInsertBlock={(position, kind, source, options) =>
          onRequestInsert?.({
            blockId: block.id,
            kind,
            position,
            source,
            headingLevel: options?.headingLevel,
          })
        }
        onTransformBlock={(kind, nextContent) => {
          void handleTransformKind(kind, nextContent);
        }}
      />
      {canInsert && (
        <div
          className={styles.blockActions}
          data-visible={showActions ? 'true' : undefined}
        >
          <button
            type="button"
            className={styles.blockActionsButton}
            aria-label="插入块"
            onMouseDown={(event) => {
              event.preventDefault();
              event.stopPropagation();
            }}
            onClick={(event) => {
              event.stopPropagation();
              onToggleInlineMenu(block.id);
            }}
          >
            <Plus size={14} />
          </button>
        </div>
      )}
      {canInsert && inlineMenuActive && (
        <div
          className={styles.inlineInsertPopover}
          ref={inlineMenuRef}
          onClick={(event) => event.stopPropagation()}
        >
          <div className={styles.inlineInsertPositionTabs}>
            <button
              type="button"
              className={`${styles.inlineInsertPositionButton} ${inlineMenuPosition === 'after' ? styles.inlineInsertPositionButtonActive : ''}`}
              onClick={(event) => {
                event.stopPropagation();
                onInlineMenuPositionChange('after');
              }}
            >
              之后
            </button>
            <button
              type="button"
              className={`${styles.inlineInsertPositionButton} ${inlineMenuPosition === 'before' ? styles.inlineInsertPositionButtonActive : ''}`}
              onClick={(event) => {
                event.stopPropagation();
                onInlineMenuPositionChange('before');
              }}
            >
              之前
            </button>
          </div>
          <BlockInsertMenuContent
            isMoreOpen={inlineMenuMoreOpen}
            onToggleMore={onToggleInlineMenuMore}
            onSelect={(item) => {
              onInlineMenuSelect(item, inlineMenuPosition);
            }}
          />
        </div>
      )}
    </div>
  );
};

export const BlockList = React.forwardRef<BlockListHandle, BlockListProps>(
  ({ blocks, isLoading = false, onBlockClick, onBlockDelete, onAddBlock }, ref) => {
    const containerRef = React.useRef<HTMLDivElement | null>(null);
    const saveHandlersRef = React.useRef<Map<string, () => Promise<void>>>(new Map());
    const [editingBlockId, setEditingBlockId] = useState<string | null>(null);
    const [isInsertMenuOpen, setIsInsertMenuOpen] = useState(false);
    const [isMoreOpen, setIsMoreOpen] = useState(false);
    const [inlineMenu, setInlineMenu] = useState<{ anchorId: string } | null>(null);
    const [inlineMenuPosition, setInlineMenuPosition] = useState<BlockInsertPosition>('after');
    const [inlineMenuMoreOpen, setInlineMenuMoreOpen] = useState(false);
    const insertMenuRef = useRef<HTMLDivElement | null>(null);
    const inlineMenuRef = useRef<HTMLDivElement>(null!);

    const registerSaveHandler = React.useCallback((blockId: string, handler: () => Promise<void>) => {
      saveHandlersRef.current.set(blockId, handler);
    }, []);

    const unregisterSaveHandler = React.useCallback((blockId: string) => {
      saveHandlersRef.current.delete(blockId);
    }, []);

    const closeAllMenus = React.useCallback(() => {
      setIsInsertMenuOpen(false);
      setIsMoreOpen(false);
      setInlineMenu(null);
      setInlineMenuMoreOpen(false);
    }, []);

    React.useEffect(() => {
      if (!isInsertMenuOpen && !inlineMenu) return;
      const handleClickOutside = (event: MouseEvent) => {
        const target = event.target as Node;
        if (insertMenuRef.current?.contains(target)) return;
        if (inlineMenuRef.current?.contains(target)) return;
        closeAllMenus();
      };
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [closeAllMenus, inlineMenu, isInsertMenuOpen]);

    React.useEffect(() => {
      if (blocks.length === 0) return;
      setInlineMenu(null);
      setInlineMenuMoreOpen(false);
    }, [blocks.length]);

    useImperativeHandle(ref, () => ({
      async saveAll() {
        if (saveHandlersRef.current.size === 0) return;
        const tasks = Array.from(saveHandlersRef.current.values()).map((handler) => handler());
        const results = await Promise.allSettled(tasks);
        const failed = results.find((result) => result.status === 'rejected');
        if (failed && failed.status === 'rejected') {
          throw failed.reason ?? new Error('保存失败');
        }
      },
    }), []);

    const handleInsertKind = (kind: BlockKind, options?: BlockInsertOptions) => {
      onAddBlock?.(kind, options);
      closeAllMenus();
    };

    const toggleInlineMenu = (anchorId: string) => {
      setInlineMenu((current) => {
        if (current && current.anchorId === anchorId) {
          setInlineMenuMoreOpen(false);
          return null;
        }
        setInlineMenuMoreOpen(false);
        setInlineMenuPosition('after');
        return { anchorId };
      });
    };

    const renderInsertMenu = () => {
      if (!onAddBlock) return null;
      return (
        <div className={styles.appendBar}>
          <button
            className={styles.appendButton}
            onClick={() => handleInsertKind('paragraph', { source: 'bottom-menu' })}
          >
            + 添加一段文字
          </button>
          <div className={styles.insertMenu} ref={insertMenuRef}>
            <button
              type="button"
              className={styles.insertMenuButton}
              onClick={() => setIsInsertMenuOpen((prev) => !prev)}
            >
              <PlusCircle size={16} /> 插入块
            </button>
            {isInsertMenuOpen && (
              <div className={styles.insertMenuPopover}>
                <BlockInsertMenuContent
                  isMoreOpen={isMoreOpen}
                  onToggleMore={() => setIsMoreOpen((prev) => !prev)}
                  onSelect={(item) =>
                    handleInsertKind(item.kind, { source: 'bottom-menu', headingLevel: item.headingLevel })
                  }
                />
              </div>
            )}
          </div>
        </div>
      );
    };

    if (isLoading) {
      return (
        <div ref={containerRef} className={styles.container}>
          <div className={styles.loading}>加载中...</div>
        </div>
      );
    }

    return (
      <div ref={containerRef} className={styles.container}>
        {/* Blocks List */}
        {blocks.length === 0 ? (
          <div className={styles.empty}>
            <p>暂无块</p>
            <p className={styles.hint}>点击下方“添加一段文字”开始创作</p>
            {renderInsertMenu()}
          </div>
        ) : (
          <div className={styles.list}>
            {blocks.map((block, index) => {
              const previousBlockId = index > 0 ? blocks[index - 1]?.id : undefined;
              return (
                <React.Fragment key={block.id}>
                  <BlockItem
                  block={block}
                  onDelete={onBlockDelete}
                  onClick={onBlockClick}
                  onRegisterSave={registerSaveHandler}
                  onUnregisterSave={unregisterSaveHandler}
                  isEditing={editingBlockId === block.id}
                  onStartEdit={(id) => setEditingBlockId(id)}
                  onExitEdit={(id) => {
                    setEditingBlockId((current) => (current === id ? null : current));
                  }}
                  onRequestInsert={(payload) =>
                    handleInsertKind(payload.kind, {
                      anchorBlockId: payload.blockId,
                      position: payload.position,
                      source: payload.source,
                      headingLevel: payload.headingLevel,
                    })
                  }
                  inlineMenuActive={inlineMenu?.anchorId === block.id}
                  inlineMenuPosition={inlineMenuPosition}
                  onInlineMenuPositionChange={setInlineMenuPosition}
                  onToggleInlineMenu={toggleInlineMenu}
                  inlineMenuMoreOpen={inlineMenuMoreOpen}
                  onToggleInlineMenuMore={() => setInlineMenuMoreOpen((prev) => !prev)}
                  inlineMenuRef={inlineMenuRef}
                  onInlineMenuSelect={(item, position) =>
                    handleInsertKind(item.kind, {
                      anchorBlockId: block.id,
                      position,
                      source: 'inline-plus',
                      headingLevel: item.headingLevel,
                    })
                  }
                  canInsert={Boolean(onAddBlock)}
                    previousBlockId={previousBlockId}
                />
                </React.Fragment>
              );
            })}
          </div>
        )}
        {blocks.length > 0 && renderInsertMenu()}
      </div>
    );
  }
);

BlockList.displayName = 'BlockList';

interface BlockInsertMenuContentProps {
  isMoreOpen: boolean;
  onToggleMore: () => void;
  onSelect: (item: InsertMenuItemConfig) => void;
}

const BlockInsertMenuContent: React.FC<BlockInsertMenuContentProps> = ({ isMoreOpen, onToggleMore, onSelect }) => (
  <>
    <InsertMenuGroup title="文本与列表" items={COMMON_INSERT_ITEMS} onSelect={onSelect} />
    <hr className={styles.insertMenuDivider} />
    <button type="button" className={styles.insertMenuMoreToggle} onClick={onToggleMore}>
      {isMoreOpen ? '隐藏更多块类型' : '更多块类型…'}
    </button>
    {isMoreOpen && (
      <>
        {EXTRA_INSERT_GROUPS.map((group) => (
          <InsertMenuGroup key={group.title} title={group.title} items={group.items} onSelect={onSelect} />
        ))}
      </>
    )}
  </>
);

interface InsertMenuGroupProps {
  title: string;
  items: InsertMenuItemConfig[];
  onSelect: (item: InsertMenuItemConfig) => void;
}

const InsertMenuGroup: React.FC<InsertMenuGroupProps> = ({ title, items, onSelect }) => (
  <div className={styles.insertMenuGroup}>
    <p className={styles.insertMenuGroupTitle}>{title}</p>
    {items.map((item) => (
      <button
        key={`${title}-${item.label}-${item.headingLevel ?? item.kind}`}
        type="button"
        className={styles.insertMenuItem}
        onClick={() => onSelect(item)}
      >
        <span className={styles.insertMenuItemLabel}>{item.label}</span>
        {item.description && <span className={styles.insertMenuItemDescription}>{item.description}</span>}
      </button>
    ))}
  </div>
);

export type { BlockInsertOptions, BlockInsertPosition, BlockInsertSource } from './insertTypes';
