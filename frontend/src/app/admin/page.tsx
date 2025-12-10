'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

/**
 * /admin 根路径占位页
 * 目前没有直接内容，统一跳转到 /admin/libraries
 * 避免用户访问 /admin 时出现 404 误解为系统故障。
 */
export default function AdminIndexRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/admin/libraries');
  }, [router]);

  return (
    <main style={{ padding: '2rem', textAlign: 'center' }}>
      <p style={{ fontSize: 14, color: 'var(--text-subtle,#666)' }}>正在跳转到库列表…</p>
    </main>
  );
}
