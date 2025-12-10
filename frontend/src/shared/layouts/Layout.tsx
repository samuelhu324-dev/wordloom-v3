import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import styles from './Layout.module.css';

interface LayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
  activeRoute?: string;
}

export const Layout: React.FC<LayoutProps> = ({ children, showSidebar = true, activeRoute }) => {
  return (
    <div className={styles.layout}>
      <Header />
      <div className={styles.container}>
        {showSidebar && <Sidebar activeRoute={activeRoute} />}
        <main className={styles.main}>{children}</main>
      </div>
    </div>
  );
};
