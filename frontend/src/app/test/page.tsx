'use client';

export default function TestPage() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>路由测试页面</h1>
      <p>如果你能看到这个页面，说明基础路由是正常的。</p>
      <p>问题在于 (admin) 路由组</p>
      <a href="/admin/libraries" style={{ color: 'blue', textDecoration: 'underline' }}>
        尝试访问 /admin/libraries
      </a>
    </div>
  );
}
