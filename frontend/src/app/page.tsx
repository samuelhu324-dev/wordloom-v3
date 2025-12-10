'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/shared/ui';

export default function HomePage() {
  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 'var(--spacing-xl)' }}>
      <div style={{ textAlign: 'center' }}>
        <h1>Welcome to Wordloom</h1>
        <p>Your knowledge management system</p>
      </div>
      <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexDirection: 'column', alignItems: 'center' }}>
        <Link href="/admin/libraries">
          <Button variant="primary" size="lg">
            Go to Admin - Libraries
          </Button>
        </Link>
        <Link href="/test">
          <Button variant="secondary" size="lg">
            Route Test Page
          </Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary" size="lg">
            Login
          </Button>
        </Link>
      </div>
      <div style={{ marginTop: '40px', fontSize: '12px', color: '#666', textAlign: 'center' }}>
        <p>如果 /admin/libraries 返回 404，但 /test 可以访问，说明问题在于 (admin) 路由组</p>
        <p>v1.0 - UI Card System Ready</p>
      </div>
    </main>
  );
}
