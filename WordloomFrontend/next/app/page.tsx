// next/src/app/home/page.tsx
import { Home as HomeIcon, Sparkles, FileText, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen p-8">
      {/* 页面头部 */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg">
            <HomeIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              Home
            </h1>
            <p className="text-sm text-muted">Welcome to Wordloom</p>
          </div>
        </div>

        {/* 功能卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="group p-6 rounded-2xl bg-card border border-border hover:border-blue-500/50 transition-all hover:shadow-lg">
            <div className="h-12 w-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
              <Sparkles className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Quick Start</h3>
            <p className="text-sm text-muted">
              Get started with Wordloom's powerful writing and editing tools in minutes.
            </p>
          </div>

          <div className="group p-6 rounded-2xl bg-card border border-border hover:border-cyan-500/50 transition-all hover:shadow-lg">
            <div className="h-12 w-12 rounded-xl bg-cyan-500/10 flex items-center justify-center mb-4 group-hover:bg-cyan-500/20 transition-colors">
              <FileText className="h-6 w-6 text-cyan-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Recent Projects</h3>
            <p className="text-sm text-muted">
              Access your recent documents and continue where you left off.
            </p>
          </div>

          <div className="group p-6 rounded-2xl bg-card border border-border hover:border-purple-500/50 transition-all hover:shadow-lg">
            <div className="h-12 w-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4 group-hover:bg-purple-500/20 transition-colors">
              <Zap className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">AI Features</h3>
            <p className="text-sm text-muted">
              Leverage AI-powered features to enhance your writing experience.
            </p>
          </div>
        </div>

        {/* 欢迎内容 */}
        <div className="mt-12 p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20 border border-blue-200/50 dark:border-blue-800/50">
          <h2 className="text-2xl font-bold mb-4">Welcome to Wordloom</h2>
          <p className="text-muted leading-relaxed mb-4">
            Wordloom is your comprehensive writing and editing hub, designed to streamline your creative process. 
            Whether you're working on a novel, blog post, or technical documentation, our tools help you write better and faster.
          </p>
          <div className="flex gap-3">
            <a
              href="/loom"
              className="px-6 py-2.5 rounded-lg bg-accent text-accent-fg hover:bg-accent/90 transition-colors font-medium"
            >
              Go to Loom
            </a>
            <a
              href="/orbit"
              className="px-6 py-2.5 rounded-lg border border-border hover:bg-accent/10 transition-colors font-medium"
            >
              Explore Orbit
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
