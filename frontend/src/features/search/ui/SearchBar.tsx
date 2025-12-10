'use client';
import React, { useState } from 'react';
import styles from './SearchBar.module.css';
import { useRouter } from 'next/navigation';

export const SearchBar: React.FC = () => {
  const [q,setQ] = useState('');
  const router = useRouter();
  return (
    <div className={styles.bar}>
      <input
        className={styles.input}
        value={q}
        onChange={e=>setQ(e.target.value)}
        placeholder="搜索 (块 / 书籍 / 标签...)"
        onKeyDown={e=>{ if(e.key==='Enter'&&q.trim()){ router.push(`/admin/search?q=${encodeURIComponent(q.trim())}`); } }}
      />
      <button
        className={styles.btn}
        disabled={!q.trim()}
        onClick={()=>router.push(`/admin/search?q=${encodeURIComponent(q.trim())}`)}
      >搜索</button>
    </div>
  );
};

export default SearchBar;