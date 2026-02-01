# ADR-154 Plan174A/B Admin UI i18n

## Status

Status: Accepted
Date: 2025-12-06
Authors: Wordloom Frontend & Platform Team (Plan174A/B)

## Context

1. **Admin UI 是双语需求的盲区。** 过去所有按钮、导航和 Toast 同时混用中英文硬编码，无法在同一页面内统一语言，更难以支撑面向全球的演示。
2. **没有可靠的语言偏好来源。** 用户设置模型缺少 ui_language 字段，前端只能临时保存浏览器 locale；一旦刷新或跨设备就回到默认中文。
3. **导航入口不具备语言切换 affordance。** 旧的粘性菜单仅包含 Theme 与 Workbox，用户很难发现可以切换语言，也无法用键盘操作。

## Decision

1. **确立 UI 级 i18n 范围。** 仅翻译 UI 文案（nav/按钮/提示/错误），Domain 数据保持原文，不新增 /en、/zh 路由。字典统一存于 `frontend/src/i18n/locales/{zh-CN,en-US}.ts`，key 命名遵循 `模块.语义`（如 `nav.language`）。
2. **落地跨切 I18nProvider。** `frontend/src/i18n/I18nContext.tsx` + `useI18n` 提供 `{lang, t, setLang}`，语言首选项写入 `localStorage('wordloom.uiLanguage')` 并在初始挂载时回填；未命中的 key 返回 key 本身防止渲染中断。
3. **Language 菜单取代旧 Libraries 链接。** `frontend/src/shared/layouts/LanguageMenu.tsx` 沿用 Theme/Workbox 的 hover 延迟、aria 契约与阴影，面板内嵌 `LanguageSwitcher` 提供 zh-CN / en-US 两个 `role="menuitemradio"` 按钮。
4. **为 Phase 2 预留用户设置字段。** DDD 规则登记 `UserSettings.ui_language: UiLanguage = 'zh-CN'` 与 `set_ui_language` 方法；Hexagonal 层记录未来通过 `/api/v1/me/settings` 同步的契约，迁移完成前禁止把 copy 写入其他聚合。

## Consequences

* **正向**：导航和按钮全部走字典，切换语言无需刷新，体验与 Theme/Workbox 保持一致。
* **正向**：语言偏好有了约定位置（localStorage + 未来 `/me/settings`），后续移动端或桌面端可共用同一字段。
* **正向**：三份 RULES 与 ADR 同步，任何尝试把翻译塞进 Domain 或路由层的需求都可以引用本 ADR 驳回。
* **负向**：首阶段仍依赖浏览器存储，用户清理缓存会回到默认语言，需要 Phase 2 完成 `/me/settings` 接入才能彻底解决。
* **负向**：所有 UI 文案都要改写为 `t()`，一次性 diff 较大，需要逐模块 rollout 并补齐测试。

## Implementation Notes

* 前端结构：`frontend/src/i18n/{config.ts, I18nContext.tsx, useI18n.ts, LanguageSwitcher.tsx, locales/}`；`frontend/src/app/providers.tsx` 将 I18nProvider 包裹在 ThemeProvider 之外，`app/layout.tsx` 把 `<html lang>` 绑定到默认语言。
* 导航集成：`frontend/src/shared/layouts/Header.tsx` 用 `t('app.title')`、`t('nav.searchPlaceholder')` 等 key 取代硬编码，并把 `LanguageMenu` 挂到 Theme 与 Workbox 之间。
* 语言菜单样式：`frontend/src/shared/layouts/LanguageMenu.module.css` 复制 Theme 菜单的触发器、圆角、阴影和 hover 规则，同时沿用 Workbox 的键盘/hover 延迟逻辑。
* 未来后端：`UserSettings` 聚合在 DDD/HEX 规则中登记 ui_language 字段与 setter，待 Phase 2 migration + `/api/v1/me/settings` 更新后再落地。

## References

* Plans: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_174A_i18nDesign.md`, `Plan_174B_i18nDesignImplementation.md`
* Rules: `assets/docs/DDD_RULES.yaml` (POLICY-I18N-PLAN174A-UI-LANGUAGE), `assets/docs/HEXAGONAL_RULES.yaml` (i18n_runtime_strategy), `assets/docs/VISUAL_RULES.yaml` (navigation_language_switcher)
* Code: `frontend/src/app/layout.tsx`, `frontend/src/app/providers.tsx`, `frontend/src/i18n/*`, `frontend/src/shared/layouts/{Header.tsx,LanguageMenu.tsx}`, `frontend/src/i18n/locales/{zh-CN,en-US}.ts`
