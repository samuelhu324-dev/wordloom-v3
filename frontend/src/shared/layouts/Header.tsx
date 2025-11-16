import React from 'react';
import Link from 'next/link';
import styles from './Header.module.css';

export const Header: React.FC = () => {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link href="/" className={styles.logo}>
          <h1>Wordloom</h1>
        </Link>
        <nav className={styles.nav}>
          <Link href="/admin/libraries">Libraries</Link>
          <Link href="/admin/bookshelves">Bookshelves</Link>
          <Link href="/admin/books">Books</Link>
          <Link href="/admin/tags">Tags</Link>
          <Link href="/admin/media">Media</Link>
          <Link href="/admin/search">Search</Link>
          <Link href="/admin/dashboard">Dashboard</Link>
        </nav>
      </div>
    </header>
  );
};
