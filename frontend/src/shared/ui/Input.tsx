'use client';

import React, { InputHTMLAttributes, forwardRef } from 'react';
import styles from './Input.module.css';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, fullWidth = false, className = '', ...props }, ref) => {
    const containerClass = [styles.inputWrapper, fullWidth ? styles['inputWrapper--full'] : '', error ? styles['inputWrapper--error'] : ''].filter(Boolean).join(' ');

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
