import React from 'react';
import type { BasementBookshelfOption, DeletedBookDto } from '@/entities/basement/types';
import { restoreBook } from '@/features/basement/api';
import { Button } from '@/shared/ui';

interface Props {
  book: DeletedBookDto;
  shelves: BasementBookshelfOption[];
  onClose: () => void;
  onSuccess?: () => void;
}

const backdropStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,.4)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalStyle: React.CSSProperties = {
  background: 'var(--surface,#fff)',
  borderRadius: 16,
  padding: '1.25rem',
  width: '420px',
  maxWidth: '90vw',
  boxShadow: '0 12px 32px rgba(15,23,42,0.2)',
};

export default function RestoreBookModal({ book, shelves, onClose, onSuccess }: Props) {
  const hasOriginalShelf = Boolean(book.original_bookshelf_id);
  const [mode, setMode] = React.useState<'original' | 'custom'>(hasOriginalShelf ? 'original' : 'custom');
  const [customShelfId, setCustomShelfId] = React.useState<string>('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | undefined>();
  const [done, setDone] = React.useState(false);

  const selectableShelves = React.useMemo(() => {
    const list = [...shelves];
    if (book.original_bookshelf_id && !list.some((s) => s.id === book.original_bookshelf_id)) {
      list.unshift({
        id: book.original_bookshelf_id,
        name: book.original_bookshelf_name ?? '原书架',
        exists: true,
      });
    }
    return list;
  }, [shelves, book.original_bookshelf_id, book.original_bookshelf_name]);

  React.useEffect(() => {
    if (customShelfId) return;
    if (selectableShelves.length > 0) {
      setCustomShelfId(selectableShelves[0].id);
    }
  }, [selectableShelves, customShelfId]);

  const effectiveShelfId = mode === 'original' ? book.original_bookshelf_id : customShelfId || undefined;
  const canSubmit = Boolean(effectiveShelfId || mode === 'original');

  const submit = async () => {
    setLoading(true);
    setError(undefined);
    try {
      await restoreBook(book.book_id, {
        target_bookshelf_id: mode === 'original' ? book.original_bookshelf_id ?? undefined : customShelfId || undefined,
      });
      setDone(true);
      onSuccess?.();
      setTimeout(onClose, 900);
    } catch (e: any) {
      setError(e?.message || '恢复失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="restore-title">
        <h2 id="restore-title" style={{ marginTop: 0 }}>恢复书籍</h2>
        <p style={{ fontSize: 14, lineHeight: 1.5 }}>
          <strong>{book.title}</strong>
          <br />
          Book ID: <code>{book.book_id}</code>
        </p>
        <div style={{ fontSize: 12, color: 'var(--text-muted,#6b7280)', marginBottom: '0.75rem' }}>
          原书架：{book.original_bookshelf_name ?? '未标记'}
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ fontSize: 13, display: 'block', fontWeight: 600 }}>恢复模式</label>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: 4 }}>
            <Button
              type="button"
              size="sm"
              variant="primary"
              disabled={!hasOriginalShelf || loading}
              onClick={() => setMode('original')}
              style={{ opacity: !hasOriginalShelf ? 0.5 : mode === 'original' ? 1 : 0.65 }}
              aria-pressed={mode === 'original'}
            >
              原书架
            </Button>
            <Button
              type="button"
              size="sm"
              variant="primary"
              disabled={loading}
              onClick={() => setMode('custom')}
              style={{ opacity: mode === 'custom' ? 1 : 0.65 }}
              aria-pressed={mode === 'custom'}
            >
              选择其他书架
            </Button>
          </div>
        </div>
        {mode === 'custom' && (
          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ fontSize: 13, display: 'block', fontWeight: 600 }}>可用书架</label>
            {selectableShelves.length === 0 ? (
              <p style={{ fontSize: 12, color: 'var(--danger,#d14343)' }}>当前书库没有可用书架，请先创建新书架。</p>
            ) : (
              <select
                value={customShelfId}
                onChange={(event) => setCustomShelfId(event.target.value)}
                style={{ width: '100%', padding: '6px 10px', borderRadius: 10, border: '1px solid #cbd5f5' }}
              >
                {selectableShelves.map((shelf) => (
                  <option key={shelf.id} value={shelf.id}>
                    {shelf.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
        {error && <div style={{ color: 'var(--danger,#d32f2f)', fontSize: 12, marginBottom: 8 }}>{error}</div>}
        {done && <div style={{ color: 'var(--accent,#3572ff)', fontSize: 12, marginBottom: 8 }}>恢复成功，正在刷新…</div>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button onClick={onClose} disabled={loading} style={{ padding: '6px 12px', borderRadius: 8 }}>
            取消
          </button>
          <Button
            type="button"
            size="sm"
            variant="primary"
            loading={loading}
            disabled={!canSubmit || loading || (mode === 'custom' && selectableShelves.length === 0)}
            onClick={submit}
          >
            确认恢复
          </Button>
        </div>
      </div>
    </div>
  );
}
