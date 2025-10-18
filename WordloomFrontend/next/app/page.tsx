import Link from "next/link";

export default function HomePage() {
  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight">Wordloom</h1>
      <p className="text-gray-600">
        欢迎回来。请从左侧菜单进入功能页面：<em>From Page</em>、<em>Insert</em>、<em>Home Admin</em>。
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link href="/from" className="rounded-xl border p-4 hover:bg-gray-50">
          <div className="text-lg">📑 From Page</div>
          <div className="text-sm text-gray-500 mt-1">按来源浏览与就地编辑</div>
        </Link>
        <Link href="/insert" className="rounded-xl border p-4 hover:bg-gray-50">
          <div className="text-lg">📚 Insert</div>
          <div className="text-sm text-gray-500 mt-1">多规则入库与预览</div>
        </Link>
        <Link href="/admin" className="rounded-xl border p-4 hover:bg-gray-50">
          <div className="text-lg">🛠️ Home Admin</div>
          <div className="text-sm text-gray-500 mt-1">全局搜索、就地编辑、批量处理</div>
        </Link>
      </div>

      {/* 预留欢迎 GIF/缩略图位（可放 /assets/static/media/gif/Wordloom_Welcome.gif） */}
      {/* <img src="/assets/static/media/gif/Wordloom_Welcome.gif" alt="Welcome" className="rounded-lg border" /> */}
    </section>
  );
}
