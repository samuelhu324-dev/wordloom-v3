'use client';

import React, { ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';
import styles from './Modal.module.css';

export interface ModalProps {
  isOpen: boolean;
  title?: string;
  subtitle?: string;
  children: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
  closeOnBackdrop?: boolean;
  showCloseButton?: boolean;
  lockScroll?: boolean;
  headingGap?: 'default' | 'compact';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  title,
  subtitle,
  children,
  onClose,
  footer,
  closeOnBackdrop = true,
  showCloseButton = true,
  lockScroll = false,
  headingGap = 'default',
}) => {
  useEffect(() => {
    if (!isOpen || !lockScroll) return undefined;
    const previousOverflow = document.body.style.overflow;
    const previousTouchAction = document.body.style.touchAction;
    const previousPaddingRight = document.body.style.paddingRight;
    const computedPaddingRight = window.getComputedStyle(document.body).paddingRight;
    const basePaddingRight = Number.parseFloat(computedPaddingRight) || 0;
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = 'hidden';
    document.body.style.touchAction = 'none';
    // If hiding the scrollbar changes layout, counter the delta with padding so the page stays still.
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${basePaddingRight + scrollbarWidth}px`;
    }

    return () => {
      document.body.style.overflow = previousOverflow;
      document.body.style.touchAction = previousTouchAction;
      document.body.style.paddingRight = previousPaddingRight;
    };
  }, [isOpen, lockScroll]);

  if (!isOpen) return null;

  const handleBackdropClick = () => {
    if (closeOnBackdrop) {
      onClose();
    }
  };

  return (
    <div className={styles.modal} onClick={handleBackdropClick} role="dialog" aria-modal="true">
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        {(title || subtitle) && (
          <div className={styles.modalHeader}>
            <div
              className={
                headingGap === 'compact'
                  ? `${styles.modalHeading} ${styles.modalHeadingCompact}`
                  : styles.modalHeading
              }
              style={headingGap === 'compact' ? { gap: '0px' } : undefined}
            >
              {title && <h2 className={styles.modalTitle}>{title}</h2>}
              {subtitle && <p className={styles.modalSubtitle}>{subtitle}</p>}
            </div>
            {showCloseButton && (
              <button className={styles.modalCloseButton} aria-label="关闭" type="button" onClick={onClose}>
                <X size={18} strokeWidth={2.25} />
              </button>
            )}
          </div>
        )}
        <div className={styles.modalBody}>{children}</div>
        {footer && <div className={styles.modalFooter}>{footer}</div>}
      </div>
    </div>
  );
};

Modal.displayName = 'Modal';
