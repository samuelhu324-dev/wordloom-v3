import React from 'react'

export interface BreadcrumbItem {
  label: string
  href?: string
  active?: boolean
}

export const Breadcrumb: React.FC<{ items: BreadcrumbItem[] }> = ({ items }) => {
  return (
    <nav aria-label="Breadcrumb" style={{ marginBottom: 12 }}>
      {items.map((item, idx) => (
        <span key={idx}>
          {item.href && !item.active ? (
            <a
              href={item.href}
              style={{ color: 'var(--color-brand-wordmark, var(--color-primary))' }}
            >
              {item.label}
            </a>
          ) : (
            <span
              style={{
                fontWeight: item.active ? 600 : 400,
                color: item.active ? 'inherit' : undefined,
              }}
            >
              {item.label}
            </span>
          )}
          {idx < items.length - 1 && <span> / </span>}
        </span>
      ))}
    </nav>
  )
}
