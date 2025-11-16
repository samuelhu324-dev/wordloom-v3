import React from 'react';
import Link from 'next/link';
import styles from './Sidebar.module.css';

interface SidebarProps {
  activeRoute?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeRoute }) => {
  const menuItems = [
    { label: 'Dashboard', href: '/admin/dashboard', icon: '📊' },
    { label: 'Libraries', href: '/admin/libraries', icon: '📚' },
    { label: 'Bookshelves', href: '/admin/bookshelves', icon: '🏷️' },
    { label: 'Books', href: '/admin/books', icon: '📖' },
    { label: 'Blocks', href: '/admin/blocks', icon: '📝' },
    { label: 'Tags', href: '/admin/tags', icon: '🔖' },
    { label: 'Media', href: '/admin/media', icon: '🖼️' },
    { label: 'Search', href: '/admin/search', icon: '🔍' },
  ];

  return (
    <aside className={styles.sidebar}>
      <nav className={styles.nav}>
        {menuItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`${styles.link} ${activeRoute === item.href ? styles.active : ''}`}
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};
