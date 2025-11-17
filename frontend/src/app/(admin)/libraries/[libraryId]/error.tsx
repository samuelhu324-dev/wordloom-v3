'use client'

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div style={{ padding: 24 }}>
      <h2>页面出错了（Library）</h2>
      <p style={{ color: '#b00' }}>{error?.message || 'Unknown error'}</p>
      <button onClick={() => reset()} style={{ marginTop: 12 }}>重试</button>
    </div>
  )
}
