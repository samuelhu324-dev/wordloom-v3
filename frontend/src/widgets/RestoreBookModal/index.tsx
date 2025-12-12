import React from 'react';
import { useI18n } from '@/i18n/useI18n';
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
  const { t } = useI18n();
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
        <h2 id="restore-title" style={{ marginTop: 0 }}>{t('basement.restoreModal.title')}</h2>
        <p style={{ fontSize: 14, lineHeight: 1.5 }}>
          <strong>{book.title}</strong>
          <br />
          {t('basement.restoreModal.bookId')} <code>{book.book_id}</code>
        </p>
        <div style={{ fontSize: 12, color: 'var(--text-muted,#6b7280)', marginBottom: '0.75rem' }}>
          {t('basement.restoreModal.originalShelf', { name: book.original_bookshelf_name ?? t('basement.restoreModal.originalShelfFallback') })}
        </div>
        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ fontSize: 13, display: 'block', fontWeight: 600 }}>{t('basement.restoreModal.restoreMode')}</label>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: 4 }}>
            <Button
              type="button"
              size="sm"
              variant="primary"
              disabled={!hasOriginalShelf || loading}
              onClick={() => setMode('original')}
              style={{ opacity: !hasOriginalShelf ? 0.5 : 1, border: mode === 'original' ? '2px solid var(--primary,#2563eb)' : '2px solid transparent' }}
              aria-pressed={mode === 'original'}
            >
              {t('basement.restoreModal.modeOriginal')}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="primary"
              disabled={loading}
              onClick={() => setMode('custom')}
              style={{ opacity: loading ? 0.5 : 1, border: mode === 'custom' ? '2px solid var(--primary,#2563eb)' : '2px solid transparent' }}
              aria-pressed={mode === 'custom'}
            >
              {t('basement.restoreModal.modeCustom')}
            </Button>
          </div>
        </div>
        {mode === 'custom' && (
          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ fontSize: 13, display: 'block', fontWeight: 600 }}>{t('basement.restoreModal.availableShelves')}</label>
            {selectableShelves.length === 0 ? (
              <p style={{ fontSize: 12, color: 'var(--danger,#d14343)' }}>{t('basement.restoreModal.noShelves')}</p>
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
        {done && <div style={{ color: 'var(--accent,#3572ff)', fontSize: 12, marginBottom: 8 }}>{t('basement.restoreModal.success')}</div>}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button onClick={onClose} disabled={loading} style={{ padding: '6px 12px', borderRadius: 8 }}>
            {t('common.cancel')}
          </button>
          <Button
            type="button"
            size="sm"
            variant="primary"
            loading={loading}
            disabled={!canSubmit || loading || (mode === 'custom' && selectableShelves.length === 0)}
            onClick={submit}
          >
            {t('basement.restoreModal.confirm')}
          </Button>
        </div>
      </div>
    </div>
  );
}
