export default function NotFound() {
  return (
    <div style={{ padding: 24 }}>
      <h2>未找到书架</h2>
      <p>请检查链接是否正确。</p>
      <a href="/admin/libraries" style={{ color: '#06c' }}>返回书库列表</a>
    </div>
  )
}
