'use client';
import React from 'react';
import { useSearchParams } from 'next/navigation';
import { useGlobalSearch } from '@/features/search/model/hooks';
import styles from './page.module.css';

export default function SearchPage(){
  const params = useSearchParams();
  const q = params.get('q') || '';
  const { data, isLoading } = useGlobalSearch(q, 20, 0);
  const result: any = data;
  return (
    <div className={styles.page}>
      <h1>搜索结果</h1>
      <p className={styles.query}>关键词：{q || '（空）'}</p>
      {isLoading && <p>加载中...</p>}
      {!isLoading && result?.items?.length === 0 && <p>无匹配结果。</p>}
      <ul className={styles.list}>
        {result?.items?.map((item: any) => (
          <li key={item.id} className={styles.item}>
            <div className={styles.line1}>
              <span className={styles.type}>{item.entity_type}</span>
              <strong className={styles.title}>{item.title || '(无标题)'}</strong>
              {item.relevance !== undefined && <span className={styles.relevance}>{item.relevance?.toFixed?.(2)}</span>}
            </div>
            {item.snippet && <div className={styles.snippet}>{item.snippet}</div>}
          </li>
        ))}
      </ul>
    </div>
  );
}