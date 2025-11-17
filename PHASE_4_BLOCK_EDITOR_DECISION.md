# 🎯 Block 编辑器技术决策 - Slate.js 选型

**决策日期**: 2025-11-16
**优先级**: 🔴 P0 - Critical Path
**状态**: ✅ DECIDED

---

## 对比分析

| 指标 | Slate.js | ProseMirror |
|------|----------|-----------|
| **学习曲线** | 中等（React-native） | 陡峭（独立系统） |
| **React 集成** | ⭐⭐⭐⭐⭐ 原生 | ⭐⭐⭐ 需要适配层 |
| **自定义性** | ⭐⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐ 中高 |
| **协同编辑** | ✅ 支持（通过 Yjs） | ✅⭐ 内置支持 |
| **社区活跃度** | ⭐⭐⭐⭐ 活跃 | ⭐⭐⭐ 稳定 |
| **Bundle 大小** | 150KB+ | 200KB+ |
| **文档质量** | ⭐⭐⭐⭐ 良好 | ⭐⭐⭐⭐⭐ 优秀 |
| **插件生态** | ⭐⭐⭐⭐ 丰富 | ⭐⭐⭐⭐⭐ 成熟 |
| **嵌套块支持** | ✅ 优秀 | ✅ 优秀 |
| **复杂度** | 中等 | 高 |

---

## 🔴 最终决策：**Slate.js**

### 理由

1. **React-First Integration** ⭐ Most Important
   - Slate 是为 React 设计的，公式就是：`Slate = contenteditable + React + TypeScript`
   - 无需学习独立的编辑器 API，直接用 React 思维
   - 完美适配 FSD 架构中的 React 组件

2. **对 Wordloom 块结构的完美支持**
   - 嵌套文档模型 = 块的树形结构
   - 每个块可以是不同类型（HEADING, TEXT, IMAGE, VIDEO, CODE, LIST）
   - 原生支持 Fractional Index 排序（通过 custom attributes）

3. **Plugin-First 架构**
   - 我们需要 6 种块类型，Slate 通过插件完美支持
   - 易于添加工具栏、菜单等
   - 易于扩展（如：协同编辑、版本历史）

4. **TypeScript 支持完美**
   - Slate 核心用 TypeScript 编写
   - 类型定义清晰，与 Wordloom FSD 严格类型要求一致

5. **学习曲线友好**
   - 对 React 开发者来说，上手快（1-2 天）
   - POC 可以 2-3 小时完成
   - 文档例子丰富（Plain text、Rich text、Tables、Images 等）

### 不选 ProseMirror 的原因

❌ **Unopinionated 架构虽好，但对我们增加复杂度**
   - 需要额外的 React 适配层
   - 学习成本高（独立的数据模型、命令系统）
   - 对 Next.js + FSD 的项目来说过度设计

❌ **虽然有内置协同编辑，但我们短期不需要**
   - Wordloom 当前是单用户编辑（用户切换时保存文档）
   - 如需协同，可通过 Yjs + Slate provider 后续集成（设计已支持）

---

## 实现计划

### Phase 4 Week 2: Slate 集成 (3-4 days)

```
Day 1: Setup + POC
├─ npm install slate react-dom
├─ Create BlockEditor.tsx (basic rich text)
├─ Support text formatting (Bold, Italic, Underline)
└─ Test with mock block data

Day 2: Block Types
├─ Create 6 block type renders
│  ├─ HeadingBlock (h1-h6)
│  ├─ TextBlock
│  ├─ ImageBlock (with upload)
│  ├─ VideoBlock (with URL)
│  ├─ CodeBlock (with syntax highlight)
│  └─ ListBlock (ul/ol)
└─ Toolbar for block type switching

Day 3: Advanced Features
├─ Marks (Bold, Italic, Underline, Link, Code)
├─ Block nesting support (as applicable)
├─ Copy/paste handling
└─ Undo/Redo

Day 4: Integration
├─ Connect to Block API (useCreateBlock, useUpdateBlock)
├─ Optimistic updates
├─ Error handling
└─ Loading states
```

### Slate 核心概念 (for Wordloom team)

```typescript
// Slate 数据结构
type Block = {
  type: 'heading' | 'text' | 'image' | 'video' | 'code' | 'list'
  children: Text[]  // 叶子节点存储实际文本
  attributes?: {    // 块特定属性
    level?: 1-6      // heading level
    url?: string     // image/video URL
    language?: string // code language
  }
}

type Text = {
  text: string
  bold?: boolean
  italic?: boolean
  underline?: boolean
}

// 编辑命令（高级）
editor.insertBlock(blockData)
editor.deleteBlock(blockId)
editor.updateBlockContent(blockId, newContent)
editor.moveBlock(blockId, newIndex)  // Fractional Index 自动计算
```

### 替代方案（如需更简单的编辑器）

⚠️ **如果 Slate 过于复杂，备选**:
- **TipTap** (基于 ProseMirror，提供 Vue/React 包装，学习曲线低)
- **BlockNote** (专为块编辑器设计，但不如 Slate 灵活)
- **Draft.js** (Meta 出品，但已停止活跃维护)

**建议**: 先用 Slate POC 试 2-3 小时，如果感觉复杂，再换 TipTap。

---

## npm 依赖

```bash
npm install slate slate-react slate-history

# 可选（用于 React 适配）
npm install @slate-react/use-editor

# 可选（用于语法高亮 - CodeBlock）
npm install highlight.js react-syntax-highlighter
```

---

## 成功指标 (Week 2 End)

✅ User can edit text content
✅ Can toggle bold, italic, underline
✅ Can switch block type (via toolbar)
✅ Can upload image + display
✅ Can paste content
✅ Changes sync to backend API
✅ Optimistic updates working

---

## 相关文档

- [Slate.js 官方文档](https://docs.slatejs.org/)
- [Slate 中文文档](https://doodlewind.github.io/slate-doc-cn/)
- [Slate 示例 - 从 Plain text 到 Rich text](https://www.slatejs.org/examples/richtext)

---

**Decision Owner**: Frontend Architecture Team
**Approved Date**: 2025-11-16
**Implementation Start**: 2025-11-23 (Phase 4 Week 2)
