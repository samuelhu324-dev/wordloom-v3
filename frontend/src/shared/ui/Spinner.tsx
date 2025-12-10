'use client';

import React, { HTMLAttributes } from 'react';
import styles from './Spinner.module.css';

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '', ...props }) => {
  const sizeClass = size === 'sm' ? styles.spinnerSmall : '';
  return (
    <div className={[styles.spinner, sizeClass, className].filter(Boolean).join(' ')} {...props} />
  );
};

Spinner.displayName = 'Spinner';
