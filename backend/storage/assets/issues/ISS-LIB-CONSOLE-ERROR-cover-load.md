---
id: ISS-LIB-CONSOLE-ERROR
title: Library 封面加载失败触发控制台报错
status: closed
created_at: 2025-12-18
resolved_at: 2025-12-19
---

## 背景

当 Library 卡片的封面 URL 失效或请求超时，页面会显示破图图标并在控制台抛出 404/ERR 相关报错。界面不会自动回退到默认渐变，占位样式同样消失，整体观感和可用性都受影响。

## 预期

- 封面加载失败时自动回退到默认渐变/占位，而不是显示破图。
- 控制台不再出现重复 error；必要时记录一次可控告警。
- Grid 卡片、List Avatar、Horizontal 卡片等所有封面入口都共用这一策略。

## 备注

- 首次记录自 ck-run-libraries-overview-2025-12-18。

## 解决

- `LibraryCoverAvatar` 与 Grid/List 封面组件统一监听 `onError`，失败时立即切换到渐变占位，避免破图。
- 错误日志改为仅记录一次 warning，常态渲染不再产生控制台 error。
- 在最新 ck-run（2025-12-19）中，`LIB-OVW-NoErrorsInConsole` 与 `LIB-OVW-CoverPlaceholder` 均通过验证，确认行为回归正常。
