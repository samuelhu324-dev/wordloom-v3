---
id: ISS-LIB-COVER-RATIO
title: Library 封面裁剪与比例规范
status: open
created_at: 2025-12-18
---

## 背景

当前 Library Overview 使用固定 16:9 封面区域，但上游上传的图片比例不一。1:1 或竖图会被强制拉伸到 16:9，结果只显示中间部分，用户难以预期最终效果，也缺少规格提示。

## 预期

- 定义可接受的上传比例与推荐尺寸，并在 UI 中给出提示（例如 16:9 / 1280×720）。
- 统一裁剪策略：保持 `object-fit: cover` 还是 Letterbox，需要写进 SPEC 并在代码中实现。
- 当比例不符合预期时，提供裁剪预览或自动加边（不再出现“只显示中间”）。
- 更新 checklist（LIB-OVW-CoverCrop 等）引用新的规格，保证后续回归有依据。

## 备注

- 首次记录自 ck-run-libraries-overview-2025-12-18。
