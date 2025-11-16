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
      <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
        <Link href="/admin/libraries">
          <Button variant="primary" size="lg">
            Go to Admin
          </Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary" size="lg">
            Login
          </Button>
        </Link>
      </div>
    </main>
  );
}
