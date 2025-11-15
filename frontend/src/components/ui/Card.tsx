/**
 * Card Component
 * Container component for grouped content
 */

import React from 'react';
import '@/styles/card.css';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(({ className = '', ...props }, ref) => {
  return <div ref={ref} className={`card ${className}`} {...props} />;
});

Card.displayName = 'Card';
