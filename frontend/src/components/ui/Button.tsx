/**
 * Button Component
 * Base button with variants (primary, secondary, outline)
 * Uses CSS Variables for theme support
 */

import React from 'react';
import '@/styles/button.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', className = '', ...props }, ref) => {
    const variantClass = `btn-${variant}`;
    const sizeClass = `btn-${size}`;
    const classes = `btn ${variantClass} ${sizeClass} ${className}`;

    return <button ref={ref} className={classes} {...props} />;
  }
);

Button.displayName = 'Button';
