1) “媒体上传/下载”的 schemas 现在放哪？（double-check 结论）

Book / Library 的“封面上传”不属于 media_router 的上传接口，它们各自有自己的封面上传 endpoint：
Library：library_router.py:485-607 的 POST /{library_id}/cover
Book：book_router.py:521-650 的 POST /{book_id}/cover
这两个接口的“业务返回结构”（LibraryDetailResponse、Book 的序列化输出）分别来自它们模块自己的 schemas（你给的两个文件方向是对的）：
/backend/api/app/modules/library/schemas.py
/backend/api/app/modules/book/schemas.py
media_router 自己的上传/下载接口在：
/backend/api/app/modules/media/routers/media_router.py（POST /images、POST /videos、GET /{media_id}、GET /{media_id}/file）
但注意：media_router 里实际使用的“请求 DTO（Pydantic BaseModel）”来自 application ports：
input.py:34-60（UploadImageRequest / UploadVideoRequest 等）
你给的 /backend/api/app/modules/media/schemas.py 确实存在，但我在仓库里查到：它目前基本 没有被 router/usecase 引用（只在 __init__.py:43 做了 re-export）。也就是说：“media.schemas.py 是一套 schema，但当前运行链路主要用的是 media.application.ports.input.py 那套”。
“媒体下载（GET /media/{id}/file）”是二进制 FileResponse：没有专门的 Pydantic schema，属于“直接返回文件流”的 endpoint。
2) schemas 对字段 / 上传内容现在做了哪些基本限制？

A) Book 模块（你给的 schemas.py）
在 /backend/api/app/modules/book/schemas.py 里能直接看到的约束（Pydantic 层）：

title：必填，min_length=1，max_length=255，并且 validator 会 strip + 拒绝空白字符串
summary：可选，max_length=1000，并 strip
priority/urgency：0-10
tag_ids：最多 3 个
cover_icon：最大长度 64，并且用正则 ^[a-z0-9\\-]+$（小写/数字/短横线）
cover_media_id：可选 UUID（用于引用 media）
B) Library 模块（你给的 schemas.py）
在 /backend/api/app/modules/library/schemas.py 里能直接看到的约束：

name：1-255，并 validator 保证非空白
description：可选，max_length=500
theme_color：会被规范化为 #rgb 或 #rrggbb，并校验必须是合法 hex
pinned_order：>= 0
tag_ids：用于 tags 更新（列表型字段）
cover_media_id：可选 UUID（同样是引用 media）
C) Media 模块（你给的 media/schemas.py）
在 /backend/api/app/modules/media/schemas.py 这套 schema 里能看到的约束（Pydantic 层）：

mime_type：枚举限制（图片只允许 image/jpeg|png|webp|gif；视频只允许 video/mp4|webm|ogg）
width/height：1-8000
duration_ms：1-7200000（2 小时）
file_size：validator 要求 > 0
批量类请求（比如 media_ids）会有 min_length/max_length 之类限制（例如最多 100）
但再次强调：这套目前不一定是“运行时实际用的那套”。

D) 真正对“上传文件内容”的限制（多发生在 router + usecase，而不是 Pydantic schema）
因为 UploadFile（multipart）本身不是用 Pydantic 校验二进制内容，所以关键限制在：

Library 封面上传 router：library_router.py:500-569
文件不能为空（读完 bytes 后判空）
MIME 类型：通过 content_type + 扩展名映射，只允许 JPEG/PNG/WEBP/GIF（不支持则 422）
文件大小 / 尺寸 / 配额：交给 Media 的 UploadImageUseCase 校验（见下）
Book 封面上传 router：book_router.py:550-606
文件不能为空
MIME 类型：同样只允许 JPEG/PNG/WEBP/GIF
“只有 Stable 且非 Legacy 才允许上传封面”（这是业务约束）
Media 的图片上传 usecase（最终兜底的强约束）：upload_image.py:27-105
支持 MIME：JPEG/PNG/WEBP/GIF
大小上限：10MB
配额：默认 1GB（used_storage + file_size > storage_quota 会报错）
尺寸（如果传了 width/height）：1-8000
Media 的视频上传 usecase：upload_video.py:28-78
支持 MIME：MP4/WEBM/OGG
大小上限：100MB
也有配额/时长等校验
建议（针对你正在思考的“schemas 放哪更合理”）

现在的状态是：Book/Library 模块 schemas 是“真正在用且合理”的；Media 模块存在“两套 schemas.py vs media/application/ports/input.py）并行”的迹象。
如果你要“定规矩”，我建议二选一：
方案 A：以 input.py 为准，把 schemas.py 逐步下线/合并（避免双轨）
方案 B：以 schemas.py 为准，让 ports/input 改为引用它（更符合“模块对外 schema 集中管理”的直觉）
不建议继续维持两套“看起来都像 schema，但只有一套真的被 router 调用”的结构，因为会让你后续补校验/写文档时产生分裂。
如果你愿意，我可以再帮你做一个“落地建议版”的 PR：把 media 的 DTO/schema 统一成一套（不改行为，只做整理与引用收敛），这样你后面写 observability/schema 文档会更顺。