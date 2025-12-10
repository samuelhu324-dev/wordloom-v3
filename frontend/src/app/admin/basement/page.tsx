"use client";
import BasementMainWidget from '@/widgets/basement/BasementMainWidget';
import styles from './page.module.css';

export default function BasementPage() {
  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <BasementMainWidget />
      </div>
    </main>
  );
}
