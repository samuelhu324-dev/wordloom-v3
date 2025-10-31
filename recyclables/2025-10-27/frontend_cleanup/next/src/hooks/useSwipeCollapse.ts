"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Options = {
  collapsedWidth?: number;   // 折叠宽度
  expandedWidth?: number;    // 展开宽度
  threshold?: number;        // 触发阈值（px）
};

export function useSwipeCollapse(opts: Options = {}) {
  const {
    collapsedWidth = 64,
    expandedWidth = 240,
    threshold = 30,
  } = opts;

  const [collapsed, setCollapsed] = useState(false);

  // SSR 安全：仅在客户端读取 window
  const isClient = typeof window !== "undefined";

  // 鼠标/触屏拖拽
  const startXRef = useRef<number | null>(null);
  const deltaRef = useRef(0);

  const onStart = useCallback((clientX: number) => {
    startXRef.current = clientX;
    deltaRef.current = 0;
  }, []);

  const onMove = useCallback((clientX: number) => {
    if (startXRef.current == null) return;
    deltaRef.current = clientX - startXRef.current;
  }, []);

  const onEnd = useCallback(() => {
    if (startXRef.current == null) return;
    const dx = deltaRef.current;
    startXRef.current = null;
    deltaRef.current = 0;

    // 右滑展开，左滑收起
    if (dx > threshold) setCollapsed(false);
    if (dx < -threshold) setCollapsed(true);
  }, [threshold]);

  // 鼠标事件
  useEffect(() => {
    if (!isClient) return;

    const onMouseDown = (ev: MouseEvent) => onStart(ev.clientX);
    const onMouseMove = (ev: MouseEvent) => onMove(ev.clientX);
    const onMouseUp = () => onEnd();

    window.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [isClient, onStart, onMove, onEnd]);

  // 触屏事件
  useEffect(() => {
    if (!isClient) return;

    const onTouchStart = (ev: TouchEvent) => onStart(ev.touches[0].clientX);
    const onTouchMove = (ev: TouchEvent) => onMove(ev.touches[0].clientX);
    const onTouchEnd = () => onEnd();

    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: true });
    window.addEventListener("touchend", onTouchEnd);
    return () => {
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("touchend", onTouchEnd);
    };
  }, [isClient, onStart, onMove, onEnd]);

  const width = collapsed ? collapsedWidth : expandedWidth;

  const toggle = useCallback(() => setCollapsed(v => !v), []);

  return { collapsed, width, toggle, setCollapsed };
}