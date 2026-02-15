Plan: 修复 Book 编辑页 Tag 保存与规则文档
TL;DR：后端 Tag 关联接口把 entity_type 当作小写枚举（library/bookshelf/book/block），前端却发送大写（BOOK），导致 422；同时 Book 更新用例本身目前只改标题等，不负责 Tag。先修正前端枚举大小写，让现有 Tag 关联接口正常工作；再视需要在应用层增加 “Book 一次性更新含 tagIds 的协调用例”。同时补充/修订三份 RULES 文档中关于 Tag 关联、枚举大小写和卡片状态带的说明。

Steps
在 frontend 中定位 Tag API 客户端（如 src/shared/api/tagApi.ts / src/entities/tag/api），把 entity_type 的 TypeScript 类型改为小写字符串联合（'library' | 'bookshelf' | 'book' | 'block'），并确保所有调用（特别是 Book 编辑弹窗）传递的是小写。
在 book 或 widgets/RestoreBookModal 等 Book 编辑弹窗组件中，确认保存逻辑是“先 PATCH /api/v1/books/{id}，再按 diff 调用 Tag associate/disassociate”；保持这个顺序，只是改用已修正的 Tag API 客户端，验证 Tag 现在能正确保存。
在 frontend 的 Book 卡片组件（例如 src/widgets/book/BookCard 或 src/entities/book/ui/BookCard）中，检查状态角标（原来显示 DRAFT/GROWING/STABLE/LEGACY）的实现，明确规则：若有 Tag，则取第一个 Tag 文本的前 7 个英文字符转大写作为角标；若无 Tag，则按 Book 成熟度字段回退到 SEED/GROWING/STABLE/LEGACY，并统一到一个公共 helper 中。
在 tag 的路由文件（如 tag_router.py）中确认 associate / disassociate 的 FastAPI 端点签名使用的是小写 EntityType 枚举；可选地增加一层防御式转换（把传入字符串 .lower() 再喂给枚举），并为非法值返回带具体错误信息的 400，而不是生硬的 422。
（可选强化）在 book 的应用层用例与 DTO（如 UpdateBookUseCase, BookUpdateDto, BookResponseDto）中设计可选的 tag_ids: list[UUID] 字段，只在应用服务里调用 Tag 模块的 AssociateTagPort/DisassociateTagPort 完成同步，保持 Book 聚合本身不保存 Tag 信息；前端再在 Book 编辑弹窗改为一次 PATCH 提交 tag_ids，不再手工循环调用 Tag 关联接口。
更新三份规则文档：在 DDD_RULES.yaml 新增/补充 Tag 相关策略（例如 POLICY-TAG-ENTITY-TYPE-CASING，规定 HTTP 传输层 entity_type 一律小写；在已有 POLICY-BOOK-TAG-BADGE-SUMMARY 中补充“Book 聚合不拥有 Tag，只消费 tags_summary 投影”）；在 HEXAGONAL_RULES.yaml 的 module_tag / module_book_ui_preview_layer 段落中写明 Tag 关联端口签名和大小写约束，以及（如果实施第 5 步）UpdateBookPort 中 tag_ids 的应用层协调职责；在 VISUAL_RULES.yaml 中增加 “Book 卡片状态角标来源于首个 Tag 的前 7 英文字符，否则按成熟度回退” 和 “Book 编辑弹窗 Tag 流程（先 Book，再 Tag 或一次性 PATCH tag_ids）” 的说明。
Further Considerations
你是更倾向于保留当前“Book PATCH + Tag 多次调用”的实现，还是希望我在计划里优先推进第 5 步那种“Book 一次 PATCH 协调 tagIds”的方案？
角标取前 7 个“英语字符”是否需要更精确的规则（例如只保留 [A-Za-z]，还是简单基于字符串长度截断