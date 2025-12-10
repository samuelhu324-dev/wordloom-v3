"use client";
import React from 'react';
import styles from './BookLayoutToggle.module.css';

interface BookLayoutToggleProps {
  layout: 'horizontal' | 'grid';
  onChange: (layout: 'horizontal' | 'grid') => void;
}

export const BookLayoutToggle: React.FC<BookLayoutToggleProps> = ({ layout, onChange }) => {
  return (
    <div className={styles.wrapper}>
      <button
        className={layout === 'horizontal' ? styles.active : styles.btn}
        onClick={() => onChange('horizontal')}
        title="横向滚动模式"
      >
        横向
      </button>
      <button
        className={layout === 'grid' ? styles.active : styles.btn}
        onClick={() => onChange('grid')}
        title="网格模式"
      >
        网格
      </button>
    </div>
  );
};
