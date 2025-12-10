/**
 * 标签颜色选择器组件
 *
 * 功能：
 * - 显示预设的颜色选项
 * - 支持自定义颜色（hex input）
 * - 即时预览选中的颜色
 */

"use client";

import { useState } from "react";

interface TagColorPickerProps {
  value: string;
  onChange: (color: string) => void;
}

// 预设颜色库
const PRESET_COLORS = [
  { name: "红色", hex: "#EF4444" },
  { name: "橙色", hex: "#F97316" },
  { name: "黄色", hex: "#EAB308" },
  { name: "绿色", hex: "#22C55E" },
  { name: "青色", hex: "#06B6D4" },
  { name: "蓝色", hex: "#3B82F6" },
  { name: "紫色", hex: "#A855F7" },
  { name: "粉色", hex: "#EC4899" },
  { name: "灰色", hex: "#6B7280" },
  { name: "黑色", hex: "#1F2937" },
];

export function TagColorPicker({ value, onChange }: TagColorPickerProps) {
  const [showCustom, setShowCustom] = useState(false);

  return (
    <div className="space-y-3">
      {/* 预设颜色 */}
      <div className="flex gap-2 flex-wrap">
        {PRESET_COLORS.map((color) => (
          <button
            key={color.hex}
            onClick={() => onChange(color.hex)}
            className={`w-8 h-8 rounded-full border-2 transition ${
              value === color.hex ? "border-gray-800 shadow-md" : "border-gray-300"
            }`}
            style={{ backgroundColor: color.hex }}
            title={color.name}
          />
        ))}
      </div>

      {/* 自定义颜色输入 */}
      <div className="flex gap-2 items-center">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-12 h-10 rounded cursor-pointer"
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
          className="flex-1 px-3 py-2 border rounded text-sm"
          pattern="^#[0-9A-Fa-f]{6}$"
        />
      </div>

      {/* 颜色预览 */}
      <div className="flex items-center gap-2">
        <div
          className="w-12 h-12 rounded border-2 border-gray-200"
          style={{ backgroundColor: value }}
        />
        <span className="text-sm text-gray-600">预览</span>
      </div>
    </div>
  );
}
