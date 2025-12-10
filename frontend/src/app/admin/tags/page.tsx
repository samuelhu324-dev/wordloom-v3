"use client";

import React, { FormEvent, useMemo, useState } from 'react';
import { Pencil, Plus, RotateCcw, Trash2 } from 'lucide-react';
import { Button, Card, CardContent, CardHeader, Input, Modal, Spinner } from '@/shared/ui';
import { showToast } from '@/shared/ui/toast';
import {
  useTagCatalog,
  useCreateTag,
  useUpdateTag,
  useDeleteTag,
  useRestoreTag,
} from '@/features/tag';
import type { TagDto } from '@/entities/tag';
import styles from './page.module.css';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';

const ORDER_OPTION_KEYS = {
  name_asc: 'tags.order.nameAsc',
  name_desc: 'tags.order.nameDesc',
  usage_desc: 'tags.order.usageDesc',
  created_desc: 'tags.order.createdDesc',
} as const;

const ORDER_OPTIONS = Object.entries(ORDER_OPTION_KEYS).map(([value, labelKey]) => ({
  value: value as keyof typeof ORDER_OPTION_KEYS,
  labelKey: labelKey as MessageKey,
}));

const PAGE_SIZE = 200;
const DEFAULT_TAG_COLOR = '#6366F1';

type OrderOption = (typeof ORDER_OPTIONS)[number]['value'];
type DialogMode = 'create' | 'edit';

interface TagFormState {
  name: string;
  color: string;
  description: string;
  icon: string;
}

const EMPTY_FORM: TagFormState = {
  name: '',
  color: DEFAULT_TAG_COLOR,
  description: '',
  icon: '',
};

const formatDate = (iso?: string | null): string => {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const formatLevelLabel = (tag: TagDto, t: (key: MessageKey, params?: Record<string, unknown>) => string): string => {
  if (tag.level <= 0) return t('tags.level.top');
  return t('tags.level.child', { level: tag.level });
};

const shortenId = (value?: string | null): string => {
  if (!value) return '—';
  return `${value.slice(0, 8)}…`;
};

const normalizeHexColor = (value?: string | null): string => {
  if (!value) return DEFAULT_TAG_COLOR;
  let hex = value.trim();
  if (!hex) return DEFAULT_TAG_COLOR;
  if (!hex.startsWith('#')) hex = `#${hex}`;
  const body = hex.slice(1);
  if (/^[0-9a-fA-F]{3}$/.test(body)) {
    hex = `#${body.split('').map((char) => `${char}${char}`).join('')}`;
  }
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) {
    return DEFAULT_TAG_COLOR;
  }
  return hex.toUpperCase();
};

const getErrorMessage = (error: unknown, fallback: string) => {
  const detail = (error as any)?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message && typeof detail.message === 'string') return detail.message;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === 'string' ? item : item?.msg || item?.message))
      .filter(Boolean);
    if (messages.length > 0) {
      return messages.join(' | ');
    }
  }
  if (typeof (error as any)?.message === 'string') {
    return (error as any).message;
  }
  return fallback;
};

export default function TagCatalogPage() {
  const [search, setSearch] = useState('');
  const [order, setOrder] = useState<OrderOption>('name_asc');
  const [onlyTopLevel, setOnlyTopLevel] = useState(true);
  const [showDeleted, setShowDeleted] = useState(false);
  const { t } = useI18n();

  const [dialogMode, setDialogMode] = useState<DialogMode>('create');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formState, setFormState] = useState<TagFormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [activeTag, setActiveTag] = useState<TagDto | null>(null);
  const [pendingAction, setPendingAction] = useState<{ id: string; type: 'delete' | 'restore' } | null>(null);

  const tagCatalog = useTagCatalog({
    page: 1,
    size: PAGE_SIZE,
    includeDeleted: showDeleted,
    onlyTopLevel,
    order,
  });
  const { data, isLoading, isFetching, isError, error, refetch } = tagCatalog;

  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();
  const restoreTagMutation = useRestoreTag();

  const isSaving = dialogMode === 'create' ? createTagMutation.isPending : updateTagMutation.isPending;

  const items = data?.items ?? [];

  const filteredItems = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return items;
    return items.filter((tag) => {
      const nameHit = tag.name.toLowerCase().includes(keyword);
      const descHit = (tag.description || '').toLowerCase().includes(keyword);
      const iconHit = (tag.icon || '').toLowerCase().includes(keyword);
      return nameHit || descHit || iconHit;
    });
  }, [items, search]);

  const totalCount = data?.total ?? items.length;
  const deletedCount = useMemo(() => items.filter((tag) => Boolean(tag.deleted_at)).length, [items]);
  const errorMessage = useMemo(() => {
    if (!error) return t('tags.error.loadFailed');
    if (typeof (error as any)?.message === 'string') return (error as any).message;
    return t('tags.error.loadFailed');
  }, [error, t]);

  const openCreateDialog = () => {
    setDialogMode('create');
    setActiveTag(null);
    setFormState({ ...EMPTY_FORM });
    setFormError(null);
    setIsDialogOpen(true);
  };

  const openEditDialog = (tag: TagDto) => {
    setDialogMode('edit');
    setActiveTag(tag);
    setFormState({
      name: tag.name ?? '',
      color: normalizeHexColor(tag.color),
      description: tag.description ?? '',
      icon: tag.icon ?? '',
    });
    setFormError(null);
    setIsDialogOpen(true);
  };

  const closeDialog = () => {
    setIsDialogOpen(false);
    setActiveTag(null);
    setFormState({ ...EMPTY_FORM });
    setFormError(null);
  };

  const handleDialogClose = () => {
    if (isSaving) return;
    closeDialog();
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = formState.name.trim();
    if (!trimmedName) {
      setFormError(t('tags.form.errors.nameRequired'));
      return;
    }

    const normalizedDescription = formState.description.trim();
    const normalizedIcon = formState.icon.trim();

    const shouldClearDescription = dialogMode === 'edit'
      && Boolean(activeTag?.description)
      && normalizedDescription.length === 0;
    const shouldClearIcon = dialogMode === 'edit'
      && Boolean(activeTag?.icon)
      && normalizedIcon.length === 0;

    const payload = {
      name: trimmedName,
      color: normalizeHexColor(formState.color),
      description: normalizedDescription.length > 0
        ? normalizedDescription
        : (shouldClearDescription ? '' : undefined),
      icon: normalizedIcon.length > 0
        ? normalizedIcon
        : (shouldClearIcon ? '' : undefined),
    };

    try {
      if (dialogMode === 'create') {
        await createTagMutation.mutateAsync(payload);
        showToast(t('tags.toast.created'));
      } else if (activeTag?.id) {
        await updateTagMutation.mutateAsync({ tagId: activeTag.id, data: payload });
        showToast(t('tags.toast.updated'));
      }
      await refetch();
      closeDialog();
    } catch (err) {
      const message = getErrorMessage(err, t('tags.toast.saveFailed'));
      setFormError(message);
      showToast(message);
    }
  };

  const handleDeleteTag = async (tag: TagDto) => {
    if (!window.confirm(t('tags.confirm.delete', { name: tag.name }))) return;
    try {
      setPendingAction({ id: tag.id, type: 'delete' });
      await deleteTagMutation.mutateAsync(tag.id);
      showToast(t('tags.toast.deleted'));
      await refetch();
    } catch (err) {
      showToast(getErrorMessage(err, t('tags.toast.deleteFailed')));
    } finally {
      setPendingAction(null);
    }
  };

  const handleRestoreTag = async (tag: TagDto) => {
    try {
      setPendingAction({ id: tag.id, type: 'restore' });
      await restoreTagMutation.mutateAsync(tag.id);
      showToast(t('tags.toast.restored'));
      await refetch();
    } catch (err) {
      showToast(getErrorMessage(err, t('tags.toast.restoreFailed')));
    } finally {
      setPendingAction(null);
    }
  };

  const isActionPending = (tag: TagDto, type: 'delete' | 'restore') => {
    if (!pendingAction || pendingAction.id !== tag.id || pendingAction.type !== type) return false;
    return type === 'delete' ? deleteTagMutation.isPending : restoreTagMutation.isPending;
  };

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <header className={styles.pageHeader}>
          <div className={styles.titleGroup}>
            <h1 className={styles.title}>{t('tags.title')}</h1>
            <p className={styles.subtitle}>{t('tags.subtitle')}</p>
          </div>
          <div className={styles.headerActions}>
            <Button size="sm" onClick={openCreateDialog}>
              <span className={styles.buttonIcon} aria-hidden="true">
                <Plus size={14} />
              </span>
              {t('tags.actions.create')}
            </Button>
          </div>
        </header>

        <div className={styles.controls}>
          <div className={styles.searchControl}>
            <Input
              placeholder={t('tags.search.placeholder')}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              fullWidth
              aria-label={t('tags.search.aria')}
            />
          </div>
          <div className={styles.toggleGroup}>
            <label className={styles.toggleItem}>
              <input
                type="checkbox"
                checked={onlyTopLevel}
                onChange={(event) => setOnlyTopLevel(event.target.checked)}
              />
              {t('tags.filters.onlyTop')}
            </label>
            <label className={styles.toggleItem}>
              <input
                type="checkbox"
                checked={showDeleted}
                onChange={(event) => setShowDeleted(event.target.checked)}
              />
              {t('tags.filters.includeDeleted')}
            </label>
            <select
              className={styles.orderSelect}
              value={order}
              onChange={(event) => setOrder(event.target.value as OrderOption)}
              aria-label={t('tags.filters.orderAria')}
            >
              {ORDER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {t(option.labelKey)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Card className={styles.catalogCard}>
          <CardHeader className={styles.catalogHeader}>
            <div>
              <h2 className={styles.catalogTitle}>{t('tags.catalog.title')}</h2>
              <p className={styles.metaSummary}>
                {t('tags.catalog.summary', { loaded: filteredItems.length, total: totalCount })}
                {showDeleted && deletedCount > 0 ? ` · ${t('tags.catalog.deleted', { count: deletedCount })}` : ''}
              </p>
            </div>
          </CardHeader>
          <CardContent className={`${styles.tableWrapper} ${styles.tableContent}`}>
            {isLoading ? (
              <div className={styles.stateBlock}>
                <Spinner />
                <p className={styles.stateText}>{t('tags.state.loading')}</p>
              </div>
            ) : isError ? (
              <div className={styles.stateBlock}>
                <p className={styles.stateTitle}>{t('tags.state.errorTitle')}</p>
                <p className={styles.stateText}>{errorMessage}</p>
                <Button size="sm" onClick={() => refetch()}>
                  {t('tags.state.retry')}
                </Button>
              </div>
            ) : filteredItems.length === 0 ? (
              <div className={styles.stateBlock}>
                <p className={styles.stateTitle}>{t('tags.state.emptyTitle')}</p>
                <p className={styles.stateText}>{t('tags.state.emptyText')}</p>
              </div>
            ) : (
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>{t('tags.table.header.tag')}</th>
                      <th>{t('tags.table.header.level')}</th>
                      <th>{t('tags.table.header.parent')}</th>
                      <th>{t('tags.table.header.usage')}</th>
                      <th>{t('tags.table.header.created')}</th>
                      <th>{t('tags.table.header.updated')}</th>
                      <th>{t('tags.table.header.status')}</th>
                      <th className={styles.actionsHeader}>{t('tags.table.header.actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.map((tag) => {
                      const isDeleting = isActionPending(tag, 'delete');
                      const isRestoring = isActionPending(tag, 'restore');
                      const deleteTooltip = isDeleting ? t('tags.table.deleting') : t('tags.table.delete');
                      const restoreTooltip = isRestoring ? t('tags.table.restoring') : t('tags.table.restore');

                      return (
                        <tr key={tag.id} className={tag.deleted_at ? styles.deletedRow : undefined}>
                          <td>
                            <div className={styles.nameCell}>
                              <span
                                className={styles.colorDot}
                                style={{ backgroundColor: tag.color || DEFAULT_TAG_COLOR }}
                                aria-hidden="true"
                              />
                              <div className={styles.tagText}>
                                <span>{tag.name}</span>
                                {tag.description ? (
                                  <span className={styles.description}>{tag.description}</span>
                                ) : null}
                              </div>
                            </div>
                          </td>
                          <td>
                            <span className={styles.levelBadge}>{formatLevelLabel(tag, t)}</span>
                          </td>
                          <td title={tag.parent_tag_id || undefined}>{shortenId(tag.parent_tag_id)}</td>
                          <td className={styles.usageCell}>{tag.usage_count}</td>
                          <td className={styles.timestamp}>{formatDate(tag.created_at)}</td>
                          <td className={styles.timestamp}>{formatDate(tag.updated_at)}</td>
                          <td>
                            <span
                              className={`${styles.statusBadge} ${tag.deleted_at ? styles.statusBadgeDeleted : styles.statusBadgeActive}`}
                            >
                              {tag.deleted_at ? t('tags.status.deleted') : t('tags.status.active')}
                            </span>
                          </td>
                          <td className={styles.actionsCell}>
                            <div className={styles.rowActions}>
                              <button
                                type="button"
                                className={styles.iconActionButton}
                                onClick={() => openEditDialog(tag)}
                                aria-label={t('tags.table.edit')}
                                data-tooltip={t('tags.table.edit')}
                              >
                                <Pencil size={14} aria-hidden="true" />
                              </button>
                              {tag.deleted_at ? (
                                <button
                                  type="button"
                                  className={styles.iconActionButton}
                                  onClick={() => handleRestoreTag(tag)}
                                  aria-label={restoreTooltip}
                                  data-tooltip={restoreTooltip}
                                  disabled={isRestoring}
                                >
                                  <RotateCcw size={14} aria-hidden="true" />
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className={`${styles.iconActionButton} ${styles.iconActionDanger}`}
                                  onClick={() => handleDeleteTag(tag)}
                                  aria-label={deleteTooltip}
                                  data-tooltip={deleteTooltip}
                                  disabled={isDeleting}
                                >
                                  <Trash2 size={14} aria-hidden="true" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Modal
        isOpen={isDialogOpen}
        title={dialogMode === 'create' ? t('tags.dialog.createTitle') : t('tags.dialog.editTitle')}
        subtitle={dialogMode === 'create' ? t('tags.dialog.createSubtitle') : activeTag?.name}
        onClose={handleDialogClose}
        closeOnBackdrop={false}
        lockScroll
        showCloseButton
        headingGap="compact"
      >
        <form className={styles.dialogForm} onSubmit={handleSubmit}>
          <Input
            label={t('tags.dialog.fields.name')}
            value={formState.name}
            onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))}
            placeholder={t('tags.dialog.fields.namePlaceholder')}
            required
          />

          <div className={styles.colorRow}>
            <div className={styles.colorPickerBlock}>
              <span className={styles.colorPickerLabel}>{t('tags.dialog.fields.color')}</span>
              <input
                type="color"
                className={styles.colorPicker}
                value={normalizeHexColor(formState.color)}
                onChange={(event) => setFormState((prev) => ({ ...prev, color: event.target.value }))}
                aria-label={t('tags.dialog.fields.colorAria')}
              />
            </div>
            <Input
              label="HEX"
              value={formState.color}
              onChange={(event) => setFormState((prev) => ({ ...prev, color: event.target.value }))}
              placeholder="#6366F1"
            />
          </div>

          <label className={styles.textareaLabel} htmlFor="tag-description">
            {t('tags.dialog.fields.description')}
            <textarea
              id="tag-description"
              className={styles.textarea}
              value={formState.description}
              onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))}
              placeholder={t('tags.dialog.fields.descriptionPlaceholder')}
              rows={3}
            />
          </label>

          <Input
            label={t('tags.dialog.fields.icon')}
            value={formState.icon}
            onChange={(event) => setFormState((prev) => ({ ...prev, icon: event.target.value }))}
            placeholder={t('tags.dialog.fields.iconPlaceholder')}
            helperText={t('tags.dialog.fields.iconHelper')}
          />

          {activeTag?.deleted_at && dialogMode === 'edit' && (
            <p className={styles.dialogNote}>{t('tags.dialog.noteDeleted')}</p>
          )}

          {formError && <p className={styles.formError}>{formError}</p>}

          <div className={styles.formFooter}>
            <Button type="button" variant="secondary" onClick={handleDialogClose} disabled={isSaving}>
              {t('tags.dialog.cancel')}
            </Button>
            <Button type="submit" loading={isSaving}>
              {dialogMode === 'create' ? t('tags.dialog.createAction') : t('tags.dialog.saveAction')}
            </Button>
          </div>
        </form>
      </Modal>
    </main>
  );
}
