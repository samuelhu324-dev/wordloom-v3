"use client";

import { useRef } from "react";

type Opts = {
  threshold?: number;           // 触发距离（px）
  onCollapse?: () => void;      // 向上/向左滑动回调
  onExpand?: () => void;        // 向下/向右滑动回调
  axis?: "x" | "y";             // 手势轴
};

/** 为任意容器增加触控手势收起/展开（简单可靠，不依赖外库） */
export function useSwipeCollapse({ threshold = 40, onCollapse, onExpand, axis = "y" }: Opts) {
  const start = useRef<number | null>(null);

  const onTouchStart = (e: React.TouchEvent) => {
    const t = e.touches[0];
    start.current = axis === "y" ? t.clientY : t.clientX;
  };

  const onTouchEnd = (e: React.TouchEvent) => {
    if (start.current == null) return;
    const t = e.changedTouches[0];
    const end = axis === "y" ? t.clientY : t.clientX;
    const delta = end - start.current;
    // y 轴：向上负值；x 轴：向左负值
    if (delta <= -threshold) onCollapse && onCollapse();
    if (delta >=  threshold) onExpand && onExpand();
    start.current = null;
  };

  return { onTouchStart, onTouchEnd };
}
