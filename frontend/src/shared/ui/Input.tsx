'use client';

import React, { InputHTMLAttributes, forwardRef } from 'react';
import styles from './Input.module.css';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  compact?: boolean;
  wrapperClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, fullWidth = false, compact = false, wrapperClassName = '', className = '', ...props }, ref) => {
    const containerClass = [
      styles.inputWrapper,
      fullWidth ? styles['inputWrapper--full'] : '',
      compact ? styles['inputWrapper--compact'] : '',
      error ? styles['inputWrapper--error'] : '',
      wrapperClassName,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className={containerClass}>
        {label && <label className={styles.inputLabel}>{label}</label>}
        <input ref={ref} className={[styles.input, className].filter(Boolean).join(' ')} {...props} />
        {error && <span className={styles.inputError}>{error}</span>}
        {helperText && !error && <span className={styles.inputHelper}>{helperText}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
