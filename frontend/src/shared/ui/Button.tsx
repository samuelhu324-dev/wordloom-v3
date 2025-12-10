'use client';

import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import styles from './Button.module.css';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      fullWidth = false,
      disabled,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const baseClasses = [styles.button, styles[`button--${variant}`], styles[`button--${size}`]].filter(Boolean).join(' ');
    const finalClasses = [baseClasses, fullWidth ? styles['button--full'] : '', className].filter(Boolean).join(' ');

    return (
      <button
        ref={ref}
        className={finalClasses}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? <span className={styles.buttonSpinner}>⟳</span> : children}
      </button>
    );
  }
);

Button.displayName = 'Button';
