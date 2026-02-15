先聚焦可交付的开发任务，再安排文档更新。

主题纯函数与封面机制落地计划
步骤
Theme 纯函数库

在 frontend/src/shared/theme/theme-pure.ts 创建纯函数集合：getStageVisual, getCoverColor, getBookTheme, mapLucideIconFromTag，读取统一配置 theme.config.ts。
getBookTheme 只依据 book.stage, book.coverIcon, book.coverColor 判定 color, icon, iconType，不触发 IO；当 stage !== 'stable' 返回 Lucide fallback（默认 book-open），stage === 'stable' 且 coverIcon 存在使用该值，否则给稳定专用 Lucide（如 award）。
getCoverColor 负责「用户指定 > 自动取色 > 默认色」三段逻辑，自动取色可先 stub（TODO 标注）或利用已有色板映射，输出 HEX 字符串。
封面颜色与 stable 封面图机制

后端 Domain：在 book.py 维护 cover_color（可选）与 cover_icon 字段；新增 set_cover_icon(url: Optional[str])、clear_cover_icon_on_downgrade(prev_stage)，仅在 stage == STABLE 且非 legacy 时允许设置/清空，并在降级触发自动清空。
成熟度用例：UpdateBookMaturityUseCase / RecalculateBookMaturityUseCase 在保存前后调用 clear_cover_icon_on_downgrade，若触发则写 Chronicle payload icon_revoked: true。
应用层上传流程：实现 UploadBookIconUseCase（或在现有 BookCommandService 中扩展）协调：
校验 Book 处于 stable。
调用 MediaUploadPort.uploadBookIcon(book_id, file) → 返回 URL（如 /media/book-icons/{bookId}.png）。
调 book.set_cover_icon(url) 并持久化。
前端 UI：在 BookEditDialog / BookContextMenu 中加入“上传封面图标”入口，仅在 stable 展示；上传成功后调用 PATCH /api/v1/books/{id} 带 cover_icon；降级后根据 DTO 中 coverIcon === null 使用 getBookTheme fallback，并弹 toast “已自动撤回封面图标”。
Media 端口与耦合控制

MediaUploadPort（backend modules/media/ports/upload.py）新增 upload_book_icon(book_id, file) -> str，由 MediaUploadAdapter 落地上传路径/鉴权；Book Domain 不依赖 Media。
前端上传统一走已有 Media API（如 POST /api/v1/media/upload），返回 URL 后再 PATCH Book，不让 Theme 或 Domain 感知 URL 结构。
规则文件更新

DDD_RULES.yaml：新增 POLICY-BOOK-COVER-ICON-STABLE-ONLY、POLICY-THEME-PURE-FUNCTION-MODULE，描述封面图标生命周期与 Theme 纯函数边界；在成熟度相关策略补充“降级自动撤销 cover_icon”。
HEXAGONAL_RULES.yaml：在 theme_runtime_strategy 写入 book_cover_icon_flow，说明 Controller→UseCase→MediaPort→Repository 链路，并强调 Theme 只消费 DTO；在成熟度段落加入 icon_side_effects。
VISUAL_RULES.yaml：扩展 book_cover_icon_visual_rules、book_maturity_visual_rules，记录 UI 启用条件、回退提示、时间线 icon_revoked 徽标。
ADR-115

在 assets/docs/ADR/ADR-115-book-theme-and-stable-cover-icon.md 记录：背景（Plan_105/106/108）、决策（Theme 纯函数 + stable-only icon + 降级撤销 + Media 解耦）、影响（优缺点、与 ADR-080/094/096/110 关系、回退提示需求）。
后续注意
自动取色算法可分阶段实现：第一版可引用固定色板映射；后期再接入真实图片分析或 Media 预处理。
若未来允许真实封面图片（非 icon），需单独 ADR 说明 Book↔Media 的强耦合与权限模型，避免与当前 “icon URL” 方案冲突。

