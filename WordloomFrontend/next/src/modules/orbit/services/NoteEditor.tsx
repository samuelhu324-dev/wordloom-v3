"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { createNote, updateNote, deleteNote, uploadTempImage, finalizeTemporaryImages } from "@/modules/orbit/domain/api";
import { createCheckpoint } from "@/modules/orbit/domain/checkpoints";
import { generateDiagram } from "@/modules/orbit/domain/diagrams";
import type { Note, Tag } from "@/modules/orbit/domain/notes";
import { MermaidDiagram } from "@/modules/orbit/ui/MermaidDiagram";
import { Image, Plus, Tag as TagIcon, X, ChevronLeft } from "lucide-react";
import { Block, createParagraphBlock, createCheckpointBlock, createImageBlock, createTextBlock, noteContentToMarkdown, markdownToNoteContent, serializeBlocks, deserializeBlocks } from "@/modules/orbit/domain/blocks";
import { BlockContainer } from "@/components/BlockRenderer";

// 动态加载标签选择器
const TagSelector = dynamic(
  () => import("@/modules/orbit/ui/TagSelector").then(mod => mod.TagSelector),
  { ssr: false, loading: () => <div className="p-3 border rounded bg-gray-50">加载标签面板中...</div> }
);

export default function NoteEditor({
  note,
  onSaved,
  onCancel,
  onDeleted
}: {
  note?: Note;
  onSaved?: (n: Note, shouldReturnToShelf?: boolean) => void;
  onCancel?: () => void;
  onDeleted?: () => void;
}) {
  const [title, setTitle] = useState(note?.title ?? "");
  const [summary, setSummary] = useState(note?.summary ?? "");
  const [summaryRows, setSummaryRows] = useState(Math.max(1, (note?.summary ?? "").split('\n').length));

  // 初始化 blocks：优先从 blocksJson 加载，否则从 markdown 解析
  const initializeBlocks = (): Block[] => {
    if (!note) {
      return [];  // 新建Note
    }

    if (note.blocksJson) {
      console.log('[NoteEditor] 从 blocksJson 加载 blocks');
      const loaded = deserializeBlocks(note.blocksJson);
      if (loaded.length > 0) {
        return loaded;
      }
    }

    if (note.text) {
      console.log('[NoteEditor] 从 text 解析 blocks，text长度:', note.text.length);
      const parsed = markdownToNoteContent(note.text);
      console.log('[NoteEditor] 解析得到', parsed.blocks.length, '个blocks');

      // 如果解析得到blocks，返回它们
      if (parsed.blocks.length > 0) {
        return parsed.blocks;
      }

      // 如果text存在但解析为空，创建一个段落block来包含原始text
      // 这防止了数据丢失
      if (note.text.trim().length > 0) {
        console.log('[NoteEditor] text存在但解析结果为空，创建段落block保留原始内容');
        return [createParagraphBlock(note.text, 0)];
      }
    }

    return [];  // 既没有 blocksJson 也没有 text
  };

  const [blocks, setBlocks] = useState<Block[]>(initializeBlocks());
  const [tags, setTags] = useState<Tag[]>(note?.tagsRel ?? []);
  const [status, setStatus] = useState(note?.status ?? "open");
  const [priority, setPriority] = useState(note?.priority ?? 3);
  const [urgency, setUrgency] = useState<number>(note?.urgency ?? 3);
  const [usageLevel, setUsageLevel] = useState<number>(note?.usageLevel ?? 3);
  const [usageCount, setUsageCount] = useState<number>(note?.usageCount ?? 0);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [generatingDiagram, setGeneratingDiagram] = useState(false);
  const [diagramCode, setDiagramCode] = useState<string | null>(null);
  const [showDiagram, setShowDiagram] = useState(false);
  const [showTagEditor, setShowTagEditor] = useState(false);

  const isEdit = Boolean(note?.id);

  // Ref to debounce block saves
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 生成完整的图像 URL
  const getImageUrl = (relativeUrl: string | null): string | null => {
    if (!relativeUrl) return null;

    // 如果已经是完整 URL，直接返回
    if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) {
      return relativeUrl;
    }

    // 获取当前位置的域名和协议
    if (typeof window !== 'undefined') {
      // 前端运行在 :3000，后端运行在 :18080
      const origin = window.location.origin;
      const backendUrl = origin.replace(':3000', ':18080');
      return `${backendUrl}${relativeUrl}`;
    }

    // 服务器端渲染时的默认值
    return `http://localhost:18080${relativeUrl}`;
  };

  // 当 note 数据更新时，同步所有状态
  useEffect(() => {
    if (note) {
      setTitle(note.title ?? "");
      setSummary(note.summary ?? "");
      setSummaryRows(Math.max(1, (note.summary ?? "").split('\n').length));

      // 重新初始化 blocks
      if (note.blocksJson) {
        console.log('[NoteEditor] useEffect: 从 blocksJson 加载 blocks');
        setBlocks(deserializeBlocks(note.blocksJson));
      } else if (note.text) {
        console.log('[NoteEditor] useEffect: 从 text 解析 blocks，text长度:', note.text.length);
        const parsed = markdownToNoteContent(note.text);
        console.log('[NoteEditor] useEffect: 解析得到', parsed.blocks.length, '个blocks');
        setBlocks(parsed.blocks);
      } else {
        setBlocks([]);
      }

      setTags(note.tagsRel ?? []);
      setStatus(note.status ?? "open");
      setPriority(note.priority ?? 3);
      setUrgency(note.urgency ?? 3);
      setUsageLevel(note.usageLevel ?? 3);
      setUsageCount(note.usageCount ?? 0);
    }
  }, [note?.id, note]);

  // Cleanup auto-save timer on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, []);

  // 添加全局 Ctrl+S 快捷键支持 - 调用完整的 onSubmit 保存所有数据
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S (Windows/Linux) 或 Cmd+S (Mac)
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        console.log('[NoteEditor] Ctrl+S 被按下，调用 onSubmit 进行完整保存');
        onSubmit();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [blocks, title, summary, tags, status, priority, urgency, note?.id]);

  // 保存 blocks 到数据库 - 使用当前的 blocks 状态
  const saveBlocksToDatabase = async (blocksToSave: Block[]) => {
    if (!note?.id) return;

    try {
      console.log('[NoteEditor] 保存 blocks 到数据库，共', blocksToSave.length, '个块');
      const blocksJson = serializeBlocks(blocksToSave);
      const markdown = noteContentToMarkdown({ blocks: blocksToSave, version: '1.0' });

      console.log('[NoteEditor] 同时发送 blocksJson 和 markdown');
      console.log('[NoteEditor] blocksJson 大小:', blocksJson.length, '字符');
      console.log('[NoteEditor] markdown 大小:', markdown.length, '字符');

      await updateNote(note.id, {
        blocksJson: blocksJson,
        text: markdown,  // 同时发送 markdown，以确保预览文本正确生成
      });
      console.log('[NoteEditor] blocks 保存成功');
    } catch (err) {
      console.error('[NoteEditor] 保存 blocks 失败:', err);
    }
  };

  // 处理块更新
  const handleUpdateBlock = (blockId: string, updatedBlock: Block) => {
    const updatedBlocks = blocks.map(b => b.id === blockId ? updatedBlock : b);
    setBlocks(updatedBlocks);

    // Debounce database save - clear previous timer if exists
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    // Set new timer to save after 1.5 seconds
    autoSaveTimerRef.current = setTimeout(() => {
      saveBlocksToDatabase(updatedBlocks);
    }, 1500);
  };

  // 处理块删除
  const handleDeleteBlock = (blockId: string) => {
    const updatedBlocks = blocks.filter(b => b.id !== blockId);
    setBlocks(updatedBlocks);

    // Debounce database save
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    autoSaveTimerRef.current = setTimeout(() => {
      saveBlocksToDatabase(updatedBlocks);
    }, 1500);
  };

  // 处理块重新排序
  const handleReorderBlocks = (fromIndex: number, toIndex: number) => {
    const newBlocks = [...blocks];
    const [movedBlock] = newBlocks.splice(fromIndex, 1);
    newBlocks.splice(toIndex, 0, movedBlock);
    setBlocks(newBlocks);

    // Debounce database save
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    autoSaveTimerRef.current = setTimeout(() => {
      saveBlocksToDatabase(newBlocks);
    }, 1500);
  };

  // 处理块插入
  const handleInsertBlock = async (type: 'checkpoint' | 'image' | 'text') => {
    switch (type) {
      case 'checkpoint':
        // 创建一个新的checkpoint，然后插入到blocks中
        if (!note?.id) {
          alert('需要先保存Note才能添加检查点');
          return;
        }
        try {
          const newCheckpoint = await createCheckpoint(note.id, {
            title: `检查点 ${new Date().toLocaleTimeString('zh-CN')}`,
            tags: [],
          });
          // 创建CheckpointBlock并保存checkpoint ID
          const newCheckpointBlock = createCheckpointBlock(newCheckpoint.id);
          setBlocks(prev => [...prev, newCheckpointBlock]);
        } catch (err) {
          console.error('创建检查点失败:', err);
          alert('创建检查点失败');
        }
        break;
      case 'text':
        // 创建一个新的文本块
        const newTextBlock = createTextBlock('', blocks.length);
        setBlocks(prev => [...prev, newTextBlock]);
        break;
      case 'image':
        handleInsertImage();
        break;
    }
  };

  // 处理图片文件 - 创建 ImageBlock
  // 业界标准：上传到临时目录，立即显示，保存笔记后 finalize
  const handleInsertImage = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      console.log('[NoteEditor] 📤 开始上传图片（临时）:', {
        name: file.name,
        type: file.type,
        size: file.size,
      });

      try {
        // 第一步：上传到临时目录（无需 note_id）
        console.log('[NoteEditor] 📤 调用 uploadTempImage');
        const { url: tempUrl, temp_id, size } = await uploadTempImage(file);
        console.log('[NoteEditor] ✓ 临时上传成功，tempUrl:', tempUrl, 'temp_id:', temp_id);

        // 第二步：创建 ImageBlock，立即显示在编辑器中
        // 注意：此时使用临时 URL，保存笔记后才会 finalize
        const newBlock = createImageBlock(tempUrl, '');
        console.log('[NoteEditor] ✓ 创建 ImageBlock:', newBlock);
        setBlocks(prev => [...prev, newBlock]);

        console.log('[NoteEditor] ✓ 图片已添加到编辑器，保存笔记时将 finalize');
        // 不需要 alert，直接在编辑器中显示即可
      } catch (error) {
        console.error('[NoteEditor] ❌ 图片上传错误:', error);
        const errorMsg = error instanceof Error ? error.message : '未知错误';
        alert(`图片上传失败: ${errorMsg}`);
      }
    };
    input.click();
  };

  async function onSubmit() {
    console.log('[NoteEditor] 🔄 onSubmit START');
    setSaving(true);
    try {
      // 将 blocks 序列化为 JSON 存储
      const blocksJson = serializeBlocks(blocks);
      // 同时保持 markdown 格式用于向后兼容和搜索
      const markdown = noteContentToMarkdown({ blocks, version: '1.0' });

      console.log('[NoteEditor] 📝 onSubmit - Saving note:', {
        title,
        blocksCount: blocks.length,
        blocksJson: blocksJson.substring(0, 100),
        markdown: markdown.substring(0, 100),
        originalText: note?.text?.substring(0, 100)
      });

      // 安全检查：如果 blocks 为空但原始 note 有 text，保留原始 text
      // 这防止了数据丢失
      let finalText = markdown;
      if (blocks.length === 0 && isEdit && note?.text) {
        console.log('[NoteEditor] 检测到 blocks 为空但原始 text 存在，保留原始 text');
        finalText = note.text;
      }

      const payload: Partial<Note> = {
        title: title || null,
        summary: summary || null,
        text: finalText,
        blocksJson, // 新增：JSON格式的blocks
        tags: tags.map(t => t.name),
        status,
        priority,
        urgency,
        // 注意：不发送 usageLevel 和 usageCount，这些是只读的
      };

      console.log('[NoteEditor] 📤 onSubmit - About to call updateNote/createNote');
      console.log('[NoteEditor] isEdit:', isEdit, 'note?.id:', note?.id);

      const saved = isEdit && note ? await updateNote(note.id, payload) : await createNote(payload);
      console.log('[NoteEditor] ✓ 笔记已保存，ID:', saved.id);

      // 第二步：收集所有临时 URL 进行 finalize
      console.log('[NoteEditor] 🔄 开始处理临时图片 finalize');
      const tempUrls = blocks
        .filter((block: Block) => block.type === 'image' && (block.content as any).url)
        .map((block: Block) => (block.content as any).url)
        .filter((url: string) => url.includes('/uploads/temp/'));

      console.log('[NoteEditor] 📊 临时图片数量:', tempUrls.length, '临时 URL:', tempUrls);

      if (tempUrls.length > 0) {
        try {
          console.log('[NoteEditor] 📤 调用 finalizeTemporaryImages');
          const finalizeResponse = await finalizeTemporaryImages(saved.id, tempUrls);
          console.log('[NoteEditor] ✓ finalize 完成:', finalizeResponse);

          // 第三步：更新 blocks 中的 URL，替换为永久 URL
          const finalized = finalizeResponse.finalized;
          const updatedBlocks = blocks.map((block: Block) => {
            if (block.type === 'image' && (block.content as any).url) {
              const oldUrl = (block.content as any).url;
              const newUrl = finalized[oldUrl];
              if (newUrl) {
                console.log('[NoteEditor] ✓ 替换图片 URL:', oldUrl, '→', newUrl);
                return {
                  ...block,
                  content: {
                    ...(block.content as any),
                    url: newUrl,
                  },
                };
              }
            }
            return block;
          });

          // 第四步：如果有 URL 被替换，再次保存笔记
          if (updatedBlocks.some((b: Block, i: number) => {
            const oldUrl = blocks[i]?.type === 'image' ? (blocks[i].content as any).url : null;
            const newUrl = b.type === 'image' ? (b.content as any).url : null;
            return oldUrl !== newUrl;
          })) {
            console.log('[NoteEditor] 📤 URL 已替换，再次保存笔记');
            setBlocks(updatedBlocks);
            const updatedBlocksJson = serializeBlocks(updatedBlocks);
            const updatedMarkdown = noteContentToMarkdown({ blocks: updatedBlocks, version: '1.0' });

            const updatePayload: Partial<Note> = {
              text: updatedMarkdown,
              blocksJson: updatedBlocksJson,
            };

            const finalSaved = await updateNote(saved.id, updatePayload);
            console.log('[NoteEditor] ✓ 笔记已更新，永久 URL 已保存');

            // 修改：保存后留在 note 页面，不返回 shelf（第二个参数改为 false）
            onSaved?.(finalSaved, false);
          } else {
            console.log('[NoteEditor] ✓ 无需更新 URL（可能没有临时图片）');
            onSaved?.(saved, false);
          }
        } catch (finalizeError) {
          console.error('[NoteEditor] ⚠️ finalize 失败，但笔记已保存:', finalizeError);
          // finalize 失败不影响笔记保存，但需要提示用户
          alert('笔记已保存，但临时图片处理失败，部分图片可能无法长期保存');
          onSaved?.(saved, false);
        }
      } else {
        console.log('[NoteEditor] ✓ 无临时图片，直接返回');
        // 修改：保存后留在 note 页面，不返回 shelf（第二个参数改为 false）
        onSaved?.(saved, false);
      }
    } catch (err) {
      console.error('[NoteEditor] ❌ onSubmit failed:', err);
      alert(`保存失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  }

  // 快速保存 Note 头部（标题/摘要/图像），不涉及 blocks，保存后留在页面
  async function onSaveNoteHeader() {
    console.log('[NoteEditor] 🔄 onSaveNoteHeader START - 点击了保存按钮');
    setSaving(true);
    try {
      if (!note?.id) {
        alert('请先创建 Note');
        return;
      }

      console.log('[NoteEditor] 📝 Saving header:', {
        title,
        summary
      });

      // 保存标题、摘要
      const payload: Partial<Note> = {
        title: title || null,
        summary: summary || null,
      };

      console.log('[NoteEditor] 📤 Calling updateNote with payload:', payload);

      // 调试：直接打印 updateNote 函数
      console.log('[NoteEditor] updateNote function type:', typeof updateNote);

      const saved = await updateNote(note.id, payload);

      console.log('[NoteEditor] ✓ updateNote 返回了结果:', saved);
      console.log('[NoteEditor] ✓ Note header saved');

      // 调用 onSaved 但不返回 shelf
      onSaved?.(saved, false);
    } catch (err) {
      console.error('[NoteEditor] Failed to save note header:', err);
      alert(`保存失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  }  async function onDeleteNote() {
    if (!isEdit || !note) return;
    if (!confirm("确定删除这个 Note 吗？此操作不可撤销。")) return;

    setDeleting(true);
    try {
      await deleteNote(note.id);
      onDeleted?.();
    } finally {
      setDeleting(false);
    }
  }

  async function onGenerateDiagram() {
    if (!isEdit || !note?.id || blocks.length === 0) return;

    setGeneratingDiagram(true);
    try {
      const result = await generateDiagram(note.id, "auto");
      setDiagramCode(result.mermaid_code);
      setShowDiagram(true);
    } catch (err) {
      console.error("Failed to generate diagram:", err);
      alert("生成结构图失败，请检查网络连接或稍后重试");
    } finally {
      setGeneratingDiagram(false);
    }
  }

  return (
    <>
    <div className="flex flex-col h-screen">
      {/* 顶部：标题栏 */}
      <div className="border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2 flex-1">
          <button
            onClick={onCancel}
            className="p-1 hover:bg-gray-100 rounded transition text-gray-700"
            title="返回书橱"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <input
              type="text"
              value={title ?? ""}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="输入标题"
              className="text-2xl font-bold outline-none w-full"
            />
            <textarea
              value={summary ?? ""}
              onChange={(e) => {
                setSummary(e.target.value);
                // 动态调整行数：计算换行符数量
                const lines = e.target.value.split('\n').length;
                setSummaryRows(Math.max(1, lines));
              }}
              placeholder="添加说明..."
              className="text-sm text-gray-600 outline-none w-full resize-none mt-1 font-normal"
              rows={summaryRows}
              style={{ lineHeight: '1.4' }}
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onSubmit}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "保存中…" : "保存"}
          </button>
          {isEdit && (
            <button
              onClick={onDeleteNote}
              disabled={deleting}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
            >
              删除
            </button>
          )}
        </div>
      </div>

      {/* 工具栏 */}
      <div className="flex gap-2 py-2 px-3 bg-white border-b border-gray-200 shadow-sm">
        {isEdit && (
          <button
            onClick={() => handleInsertBlock('checkpoint')}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded transition"
            title="插入检查点"
          >
            <Plus className="w-4 h-4" />
            检查点
          </button>
        )}

        <button
          onClick={() => handleInsertBlock('text')}
          className="flex items-center gap-1 px-3 py-1 text-sm bg-green-500 hover:bg-green-600 text-white rounded transition"
          title="插入文本框"
        >
          <Plus className="w-4 h-4" />
          文本框
        </button>

        <button
          onClick={handleInsertImage}
          className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded transition"
          title="插入图片"
        >
          <Image className="w-4 h-4" />
          图片
        </button>

        <button
          onClick={() => setShowTagEditor(true)}
          className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded transition"
          title="编辑标签"
        >
          <TagIcon className="w-4 h-4" />
          标签
        </button>

        <div className="flex-1" />

        {isEdit && (
          <button
            onClick={onGenerateDiagram}
            disabled={generatingDiagram || blocks.length === 0}
            className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {generatingDiagram ? "生成中…" : "📊"}
          </button>
        )}
      </div>

      {/* BlockManager - 主要内容区域 */}
      <div className="flex-1 p-4">
        <BlockContainer
          blocks={blocks}
          onUpdateBlock={handleUpdateBlock}
          onDeleteBlock={handleDeleteBlock}
          onReorderBlocks={handleReorderBlocks}
          noteId={note?.id}
          fallbackText={note?.text}
          onSave={onSubmit}
        />
      </div>
    </div>
      {/* Tag 编辑弹窗 */}
      {showTagEditor && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-24"
          onClick={() => setShowTagEditor(false)}
        >
          <div
            className="w-full max-w-lg bg-white rounded-lg shadow-xl border overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-medium">编辑标签</h3>
              <button onClick={() => setShowTagEditor(false)} className="p-1">
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            <div className="p-4">
              <TagSelector selectedTags={tags} onTagsChange={setTags} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}