import React from 'react';
import { useLibraries } from '@/features/library';
import { LibraryList, LibraryForm } from '@/features/library';
import { Button } from '@/shared/ui';
import styles from './LibraryMainWidget.module.css';

interface LibraryMainWidgetProps {
  onSelectLibrary?: (libraryId: string) => void;
}

export const LibraryMainWidget = React.forwardRef<HTMLDivElement, LibraryMainWidgetProps>(
  ({ onSelectLibrary }, ref) => {
    const { data: libraries, isLoading } = useLibraries();
    const [isFormOpen, setIsFormOpen] = React.useState(false);

    return (
      <div ref={ref} className={styles.widget}>
        <div className={styles.header}>
          <h2>Libraries</h2>
          <Button variant="primary" onClick={() => setIsFormOpen(true)}>
            + New
          </Button>
        </div>
        <LibraryList libraries={libraries || []} isLoading={isLoading} onSelectLibrary={onSelectLibrary} />
        <LibraryForm isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} />
      </div>
    );
  }
);

LibraryMainWidget.displayName = 'LibraryMainWidget';
