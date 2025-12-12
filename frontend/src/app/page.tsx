'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/shared/ui';
import { useI18n } from '@/i18n/useI18n';

export default function HomePage() {
  const { t } = useI18n();

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 'var(--spacing-xl)' }}>
      <div style={{ textAlign: 'center' }}>
        <h1>{t('home.title')}</h1>
        <p>{t('home.subtitle')}</p>
      </div>
      <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexDirection: 'column', alignItems: 'center' }}>
        <Link href="/admin/libraries">
          <Button variant="primary" size="lg">
            {t('home.cta.admin')}
          </Button>
        </Link>
        <Link href="/test">
          <Button variant="secondary" size="lg">
            {t('home.cta.test')}
          </Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary" size="lg">
            {t('home.cta.login')}
          </Button>
        </Link>
      </div>
      <div style={{ marginTop: '40px', fontSize: '12px', color: '#666', textAlign: 'center' }}>
        <p>{t('home.notice.admin404')}</p>
        <p>{t('home.footer.version')}</p>
      </div>
    </main>
  );
}
