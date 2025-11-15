// app/(auth)/layout.tsx
// ✅ 认证路由布局（不显示 sidebar）

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="auth-layout">
      {children}
    </div>
  );
}
