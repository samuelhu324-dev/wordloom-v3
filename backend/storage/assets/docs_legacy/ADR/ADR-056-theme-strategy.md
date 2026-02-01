// ADR-FR-001-theme-strategy.md
// ✅ 前端主题策略决策记录

# ADR-FR-001: Frontend Theme Strategy

## 状态
✅ ACCEPTED (2025-11-15)

## 背景
Wordloom 前端需要灵活的主题系统，支持：
- 多个预定义主题（Light, Dark, Loom）
- 浅色/深色模式切换
- 零硬编码颜色值
- 运行时动态切换（无需刷新）
- 用户偏好持久化

## 决策
采用 **CSS Variables + 运行时注入** 方案

### 为什么不用 Tailwind CSS?
- ❌ Tailwind 的动态类在构建时就被提取
- ❌ 主题切换需要重新编译 CSS
- ✅ CSS Variables 支持运行时改变，无需刷新

### 核心设计
1. **主题定义**：`lib/themes.ts` 中定义 3 个主题的颜色值
2. **生成 CSS Variables**：`generateCSSVariables()` 将主题对象转为 `:root { --color-*: ... }`
3. **动态注入**：`ThemeProvider` 在 useEffect 中将样式字符串注入到 `<style>` 标签
4. **持久化**：用 localStorage 保存用户选择（wl_theme, wl_mode）

### 3 个主题

| 主题 | 说明 | 品牌色 |
|------|------|--------|
| **Light** | 标准亮色，日间使用 | #1F2937 (深灰) |
| **Dark** | 标准暗色，夜间使用 | #F3F4F6 (浅白) |
| **Loom** | Wordloom 专用灰蓝风格 | #2C3E50 (灰蓝) |

每个主题都有 light 和 dark 两种模式。

## 实施细节

### 文件结构
```
frontend/src/
├── lib/themes.ts              # 3 个主题定义
├── components/providers/
│   └── ThemeProvider.tsx      # CSS Variables 注入
└── styles/
    ├── tokens.css             # CSS Variables 占位符
    ├── button.css             # 使用 var(--color-*)
    └── ...
```

### 核心代码
```typescript
// lib/themes.ts
export function generateCSSVariables(theme: ThemeToken, mode: ThemeMode): string {
  // 生成 :root { --color-primary: ...; ... }
}

// components/providers/ThemeProvider.tsx
useEffect(() => {
  const css = generateCSSVariables(theme, currentMode);
  styleEl.textContent = css;  // 动态注入
}, [currentTheme, currentMode]);
```

## 优势
✅ 零硬编码颜色值
✅ 运行时切换，平滑过渡
✅ 支持 SSR（有水合逻辑避免闪烁）
✅ localStorage 持久化
✅ 易于扩展（添加新主题只需在 THEMES 对象中添加）

## 劣势
⚠️ 需要所有颜色都用 CSS Variables（没有例外）
⚠️ 不支持 Tailwind 的 variant（如 hover:bg-red-500）

## 未来扩展（Phase B）
后端完成 `/profile/theme-preference` 后，前端可保存用户主题选择到数据库。

## 参考
- `assets/docs/VISUAL_RULES.yaml` - 完整的前端规则
- `DDD_RULES.yaml` - 后端业务规则
- `HEXAGONAL_RULES.yaml` - 后端架构规则
