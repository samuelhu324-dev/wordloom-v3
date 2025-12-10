"use client";
import React from 'react';
import Link from 'next/link';
import { useI18n } from '@/i18n/useI18n';
import { WorkboxMenu } from './WorkboxMenu';
import { ThemeMenu } from './ThemeMenu';
import { LanguageMenu } from './LanguageMenu';
import styles from './Header.module.css';

export const Header: React.FC = () => {
  const { t } = useI18n();

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo}>
          <h1>{t('app.title')}</h1>
        </Link>
        <nav className={styles.nav}>
          <ThemeMenu />
          <LanguageMenu />
          {/* Workbox 下拉菜单 */}
          <WorkboxMenu />
        </nav>
      </div>
    </header>
  );
};