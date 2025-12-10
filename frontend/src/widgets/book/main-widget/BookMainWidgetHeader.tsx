import React, { type ReactNode } from 'react';
import { LayoutGrid, List } from 'lucide-react';
import { useI18n } from '@/i18n/useI18n';
import { Button } from '@/shared/ui';
import styles from '../BookMainWidget.module.css';
import type { BookViewMode } from './maturity';

interface BookMainWidgetHeaderProps {
  heading?: string | null;
  viewMode: BookViewMode;
  onViewModeChange: (mode: BookViewMode) => void;
  showCreate: boolean;
  createPending: boolean;
  onToggleCreate: () => void;
  hideInternalActions?: boolean;
  searchSlot?: ReactNode;
  viewModeControls?: ReactNode;
}

export const BookMainWidgetHeader: React.FC<BookMainWidgetHeaderProps> = ({
  heading,
  viewMode,
  onViewModeChange,
  showCreate,
  createPending,
  onToggleCreate,
  hideInternalActions,
  searchSlot,
  viewModeControls,
}) => {
  const { t } = useI18n();
  const resolvedHeading = heading === null ? null : heading ?? t('books.widget.heading');
  const toggleLabel = showCreate ? t('button.cancel') : t('books.actions.addBook');
  const viewGroupAria = t('books.filter.view.aria');
  const gridLabel = t('books.actions.gridView');
  const listLabel = t('books.actions.listView');

  return (
    <div className={styles.widgetHeaderArea}>
      <div className={styles.widgetHeaderRow}>
        {resolvedHeading ? <h3 className={styles.headingLabel}>{resolvedHeading}</h3> : null}
        {!hideInternalActions && (
          <div className={styles.headingActions}>
            <div className={styles.searchButtonRow}>
              {searchSlot}
              <Button
                variant="primary"
                size="sm"
                onClick={onToggleCreate}
                disabled={createPending}
              >
                {toggleLabel}
              </Button>
            </div>
            <div className={styles.viewToggleRow}>
              {viewModeControls}
              <div className={styles.viewToggle} role="group" aria-label={viewGroupAria}>
                <button
                  type="button"
                  aria-label={gridLabel}
                  className={styles.viewToggleIconButton}
                  data-active={viewMode === 'showcase' ? 'true' : undefined}
                  onClick={() => onViewModeChange('showcase')}
                >
                  <LayoutGrid size={16} strokeWidth={1.8} />
                </button>
                <button
                  type="button"
                  aria-label={listLabel}
                  className={styles.viewToggleIconButton}
                  data-active={viewMode === 'row' ? 'true' : undefined}
                  onClick={() => onViewModeChange('row')}
                >
                  <List size={16} strokeWidth={1.8} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
