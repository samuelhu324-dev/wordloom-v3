"use client";

import { useEffect, useRef, useState } from "react";

interface MermaidDiagramProps {
  code: string;
  title?: string;
}

export function MermaidDiagram({ code, title }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!containerRef.current || !code) {
      setLoading(false);
      return;
    }

    const renderDiagram = async () => {
      try {
        setError(null);
        setLoading(true);

        // 动态导入 mermaid（仅浏览器端）
        const mermaidModule = await import("mermaid");
        const mermaid = mermaidModule.default || mermaidModule;

        // 初始化 mermaid
        if (mermaid.initialize) {
          mermaid.initialize({
            startOnLoad: false,
            theme: "default",
            securityLevel: "loose"
          });
        }

        // 渲染
        if (mermaid.render) {
          const { svg } = await mermaid.render("mermaid-diagram-" + Date.now(), code);

          // 清空容器并添加新的 SVG
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to render diagram";
        setError(message);
        console.error("Mermaid rendering error:", err);
      } finally {
        setLoading(false);
      }
    };

    renderDiagram();
  }, [code]);

  if (loading) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-500">
        📊 结构图生成中…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded text-sm text-red-600">
        <p className="font-semibold">📊 结构图渲染失败</p>
        <p className="text-xs mt-1">{error}</p>
      </div>
    );
  }

  if (!code) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded text-sm text-gray-500">
        暂无结构图
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {title && <p className="text-xs font-semibold text-gray-600">{title}</p>}
      <div
        ref={containerRef}
        className="overflow-x-auto bg-white p-4 rounded border border-gray-200 flex justify-center min-h-[200px]"
      >
        {/* Mermaid SVG 将被渲染到这里 */}
      </div>
    </div>
  );
}
