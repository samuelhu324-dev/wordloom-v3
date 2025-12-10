'use client';

import React, { HTMLAttributes, forwardRef } from 'react';
import styles from './Card.module.css';

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={[styles.card, className].filter(Boolean).join(' ')} {...props} />
  )
);
Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={[styles.cardHeader, className].filter(Boolean).join(' ')} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={[styles.cardContent, className].filter(Boolean).join(' ')} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={[styles.cardFooter, className].filter(Boolean).join(' ')} {...props} />
  )
);
CardFooter.displayName = 'CardFooter';
